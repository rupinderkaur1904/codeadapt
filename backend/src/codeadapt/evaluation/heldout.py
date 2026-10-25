"""Held-out synthetic cases: submissions whose bug is known by construction (methodology §6.1)."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

CORRECT = "correct"
UNMODELLED = "unmodelled"
MANIFEST = "cases.toml"


class HeldoutCase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    problem: str
    file: str = Field(pattern=r"^[A-Za-z0-9_]{1,64}\.cpp$")
    # An error-model key of `problem`, "correct", or "unmodelled".
    truth: str
    note: str = ""
    source: str = Field(repr=False)


def load_heldout(root: Path, problems: set[str] | None = None) -> list[HeldoutCase]:
    """Every case under `root/<slug>/cases.toml`, sorted by problem then file."""
    cases: list[HeldoutCase] = []
    for manifest in sorted(root.glob(f"*/{MANIFEST}")):
        data = tomllib.loads(manifest.read_text())
        slug = data["problem"]
        if slug != manifest.parent.name:
            raise ValueError(f"{manifest}: problem {slug!r} must equal the directory name")
        if problems is not None and slug not in problems:
            continue
        for entry in data.get("cases", []):
            source = (manifest.parent / entry["file"]).read_text()
            cases.append(HeldoutCase(problem=slug, source=source, **entry))
    return sorted(cases, key=lambda c: (c.problem, c.file))
