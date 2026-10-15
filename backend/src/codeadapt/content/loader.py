"""Load a problem directory into a validated, content-addressed `LoadedProblem`."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from codeadapt.content.models import ErrorModelSpec, ProblemSpec
from codeadapt.execution.models import SourceFile

PROBLEM_FILE = "problem.toml"
_MAX_FILE_BYTES = 256 * 1024


class ContentError(ValueError):
    """A problem definition is malformed. The message names the problem directory."""


@dataclass(frozen=True)
class LoadedProblem:
    spec: ProblemSpec
    root: Path
    # sha256 over every file the definition references, plus problem.toml itself.
    # Evidence records reference this, so any content change yields a new version.
    version: str
    statement: str
    harness: str
    reference: str
    error_model_sources: dict[str, str]

    def harness_file(self) -> SourceFile:
        return SourceFile(name="harness.cpp", content=self.harness)

    def program(self, solution_source: str) -> list[SourceFile]:
        """Files to compile for a candidate implementation (student code, reference, model)."""
        return [
            SourceFile(name=self.spec.solution_file, content=solution_source),
            self.harness_file(),
        ]

    def error_model(self, key: str) -> ErrorModelSpec:
        for model in self.spec.error_models:
            if model.key == key:
                return model
        raise KeyError(key)


def _read(root: Path, rel: str) -> bytes:
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ContentError(f"{root}: {rel!r} escapes the problem directory")
    if not path.is_file():
        raise ContentError(f"{root}: missing file {rel!r}")
    data = path.read_bytes()
    if len(data) > _MAX_FILE_BYTES:
        raise ContentError(f"{root}: {rel!r} exceeds {_MAX_FILE_BYTES} bytes")
    return data


def load_problem(root: Path) -> LoadedProblem:
    raw_toml = _read(root, PROBLEM_FILE)
    try:
        data = tomllib.loads(raw_toml.decode("utf-8"))
        spec = ProblemSpec.model_validate(data)
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ContentError(f"{root}: cannot parse {PROBLEM_FILE}: {exc}") from exc
    except ValidationError as exc:
        raise ContentError(f"{root}: invalid {PROBLEM_FILE}: {exc}") from exc
    if spec.slug != root.name:
        raise ContentError(f"{root}: slug {spec.slug!r} must equal the directory name")

    files = {PROBLEM_FILE: raw_toml}
    for rel in (spec.statement, spec.harness, spec.reference, *(m.file for m in spec.error_models)):
        files[rel] = _read(root, rel)

    digest = hashlib.sha256()
    for rel in sorted(files):
        digest.update(rel.encode() + b"\0" + hashlib.sha256(files[rel]).digest())

    def text(rel: str) -> str:
        try:
            return files[rel].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContentError(f"{root}: {rel!r} is not UTF-8") from exc

    return LoadedProblem(
        spec=spec,
        root=root,
        version=digest.hexdigest(),
        statement=text(spec.statement),
        harness=text(spec.harness),
        reference=text(spec.reference),
        error_model_sources={m.key: text(m.file) for m in spec.error_models},
    )


def load_catalogue(content_dir: Path) -> list[LoadedProblem]:
    """Every problem directory (one containing problem.toml) directly under `content_dir`."""
    return [
        load_problem(child)
        for child in sorted(content_dir.iterdir())
        if child.is_dir() and (child / PROBLEM_FILE).is_file()
    ]
