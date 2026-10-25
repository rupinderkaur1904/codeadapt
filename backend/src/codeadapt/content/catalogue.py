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
        """Register every current problem version (append-only; old versions are kept).

        Each current version also gets its skill-map snapshot, including versions registered
        before snapshots existed. A version's content is fixed by its hash, so its snapshot
        never changes once written.
        """
        from codeadapt.adaptation.skillmap import SkillMap

        known = {row.version: row for row in session.scalars(select(ProblemVersion))}
        for p in self.problems:
            snapshot = SkillMap.from_spec(p.spec, p.version).model_dump(mode="json")
            row = known.get(p.version)
            if row is None:
                session.add(
                    ProblemVersion(
                        version=p.version,
                        slug=p.spec.slug,
                        family=p.spec.family,
                        title=p.spec.title,
                        skill_map=snapshot,
                    )
                )
            elif row.skill_map is None:
                row.skill_map = snapshot
        try:
            session.commit()
        except IntegrityError:  # another process (API or worker) registered it concurrently
            session.rollback()
