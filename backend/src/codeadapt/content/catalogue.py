"""The set of problems this process can serve, indexed by slug and by content version."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from codeadapt.content.loader import LoadedProblem, load_catalogue
from codeadapt.db.models import ProblemVersion


@dataclass
class Catalogue:
    problems: list[LoadedProblem]
    by_slug: dict[str, LoadedProblem] = field(init=False)
    by_version: dict[str, LoadedProblem] = field(init=False)

    def __post_init__(self) -> None:
        self.by_slug = {p.spec.slug: p for p in self.problems}
        self.by_version = {p.version: p for p in self.problems}

    @classmethod
    def load(cls, content_dir: Path) -> Catalogue:
        return cls(load_catalogue(content_dir))

    def sync(self, session: Session) -> None:
        """Register every current problem version (append-only; old versions are kept)."""
        known = set(session.scalars(select(ProblemVersion.version)))
        for p in self.problems:
            if p.version not in known:
                session.add(
                    ProblemVersion(
                        version=p.version,
                        slug=p.spec.slug,
                        family=p.spec.family,
                        title=p.spec.title,
                    )
                )
        try:
            session.commit()
        except IntegrityError:  # another process (API or worker) registered it concurrently
            session.rollback()
