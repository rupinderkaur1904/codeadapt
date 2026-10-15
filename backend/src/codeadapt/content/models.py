"""Problem definitions: the authored side of a diagnostic problem.

The on-disk format (``problem.toml`` + C++ files) is documented in docs/content-format.md.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

_KEY = r"^[a-z][a-z0-9_]{0,63}$"
_SLUG = r"^[a-z][a-z0-9-]{0,63}$"
_REL_FILE = re.compile(r"^(?!.*\.\.)[A-Za-z0-9_][A-Za-z0-9_./-]{0,127}$")


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Visibility(StrEnum):
    SAMPLE = "sample"  # input and expected output may be shown to students
    HIDDEN = "hidden"  # only `student_description` may be shown


class TestCase(_Strict):
    __test__ = False  # not a pytest class

    key: str = Field(pattern=_KEY)
    input: str
    expected: str  # author's expected stdout; checked against the executed reference
    probes: tuple[str, ...] = Field(min_length=1)
    visibility: Visibility = Visibility.HIDDEN
    student_description: str = Field(min_length=1)


class ErrorModelSpec(_Strict):
    key: str = Field(pattern=_KEY)
    file: str
    skill: str
    description: str = Field(min_length=1)  # researcher-facing
    student_hint: str = Field(min_length=1)  # shown only after a supported diagnosis


class ProblemSpec(_Strict):
    slug: str = Field(pattern=_SLUG)
    title: str = Field(min_length=1)
    family: str = Field(pattern=_SLUG)
    statement: str
    harness: str
    reference: str
    solution_file: str = Field(pattern=r"^[A-Za-z0-9_]{1,64}\.cpp$")
    interface: str
    skills: dict[str, str] = Field(min_length=1)
    probes: dict[str, tuple[str, ...]] = Field(min_length=1)
    tests: tuple[TestCase, ...] = Field(min_length=1)
    error_models: tuple[ErrorModelSpec, ...] = ()

    @model_validator(mode="after")
    def _cross_references(self) -> Self:
        problems: list[str] = []
        for name in (
            self.statement,
            self.harness,
            self.reference,
            *(m.file for m in self.error_models),
        ):
            if not _REL_FILE.fullmatch(name):
                problems.append(f"unsafe or invalid relative path {name!r}")
        for key in self.skills:
            if not re.fullmatch(_KEY, key):
                problems.append(f"invalid skill key {key!r}")
        for probe, skills in self.probes.items():
            if not re.fullmatch(_KEY, probe):
                problems.append(f"invalid probe key {probe!r}")
            problems += [
                f"probe {probe!r}: unknown skill {s!r}" for s in skills if s not in self.skills
            ]
        test_keys = [t.key for t in self.tests]
        problems += [
            f"duplicate test key {k!r}" for k in sorted(set(test_keys)) if test_keys.count(k) > 1
        ]
        for test in self.tests:
            problems += [
                f"test {test.key!r}: unknown probe {p!r}"
                for p in test.probes
                if p not in self.probes
            ]
        model_keys = [m.key for m in self.error_models]
        problems += [
            f"duplicate error model key {k!r}"
            for k in sorted(set(model_keys))
            if model_keys.count(k) > 1
        ]
        for model in self.error_models:
            if model.skill not in self.skills:
                problems.append(f"error model {model.key!r}: unknown skill {model.skill!r}")
        if self.solution_file == "harness.cpp":
            problems.append("solution_file must not be named harness.cpp")
        if not any(t.visibility is Visibility.SAMPLE for t in self.tests):
            problems.append("at least one sample test is required")
        if problems:
            raise ValueError("; ".join(problems))
        return self

    def skills_probed_by(self, test: TestCase) -> set[str]:
        return {skill for probe in test.probes for skill in self.probes[probe]}
