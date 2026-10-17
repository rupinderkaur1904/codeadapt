"""Per-content-version snapshot of how tests and error models map to skills (ADR-023, D4).

Skill attribution is a modelling assumption stored with the content. Changing a problem's
probes or models creates a new content version, so an attempt is always attributed with
the snapshot of the version it was diagnosed against, never with today's content. An
attempt whose version has no snapshot contributes no skill evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict

from codeadapt.content.models import ProblemSpec

SKILL_MAP_FORMAT = 1


class SkillMap(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format: int = SKILL_MAP_FORMAT
    problem_slug: str
    problem_version: str
    # Test key -> the skills its probes name.
    test_skills: dict[str, tuple[str, ...]]
    # Error model key -> its skill.
    model_skills: dict[str, str]
    # Models whose diagnoses carry a documented collision (`known_limitation`).
    documented_collisions: tuple[str, ...] = ()

    @classmethod
    def from_spec(cls, spec: ProblemSpec, version: str) -> SkillMap:
        return cls(
            problem_slug=spec.slug,
            problem_version=version,
            test_skills={t.key: tuple(sorted(spec.skills_probed_by(t))) for t in spec.tests},
            model_skills={m.key: m.skill for m in spec.error_models},
            documented_collisions=tuple(
                sorted(m.key for m in spec.error_models if m.known_limitation)
            ),
        )

    @classmethod
    def from_stored(cls, data: Mapping[str, Any] | None) -> SkillMap | None:
        """Parse a stored snapshot; an unknown format is treated as no snapshot."""
        if not data or data.get("format") != SKILL_MAP_FORMAT:
            return None
        return cls.model_validate(data)

    def skills_of(self, test_key: str) -> tuple[str, ...]:
        return self.test_skills.get(test_key, ())


def current_skill_maps(problems: Mapping[str, ProblemSpec]) -> dict[str, SkillMap]:
    """Snapshots of the current specs, keyed by slug.

    Only for attempts that carry no content version (pure synthetic trajectories); stored
    attempts always resolve through their own version's snapshot.
    """
    return {slug: SkillMap.from_spec(spec, "") for slug, spec in problems.items()}
