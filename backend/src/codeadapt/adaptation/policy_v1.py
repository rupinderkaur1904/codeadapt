"""Adaptive policy v1: transparent selection rules over the evidence ledger.

The rules are the rows of the table in docs/methodology.md §5; keep them in sync. Every
recommendation records why it was made and, where the rule claims one, the success
criterion the follow-up attempt will be evaluated against.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from codeadapt.adaptation.ledger import SkillMaps, build_ledger, reliable_count, tests_probing
from codeadapt.adaptation.models import (
    Action,
    AttemptRecord,
    Recommendation,
    Rule,
    SuccessCriterion,
)
from codeadapt.content.models import ProblemSpec
from codeadapt.diagnosis.models import Outcome

_ABSTAINED = {
    Outcome.UNMODELLED_BEHAVIOUR,
    Outcome.INSUFFICIENT_EVIDENCE,
    Outcome.UNRELIABLE_EVIDENCE,
}


@dataclass(frozen=True)
class PolicyV1:
    name: str = "rule_policy"
    # 1.1: the ledger counts only diagnosis-explained failures (ADR-019).
    # 1.2 (ADR-023): qualified diagnoses add no failure evidence; attempts are attributed
    # with their own content version's skill map.
    # 1.3 (CE1 decision E2): only problems marked `recommendable` are candidates. The rules
    # are unchanged; a non-recommendable index problem can still be the retry fallback.
    # 1.4 (ADR-027, option P1): `non_termination_observed` is a symptom; it gets a retry of
    # the same problem with a review flag, no target skill and no criterion. Every outcome
    # now has an explicit rule; none falls through to the no-failure branch.
    version: str = "1.4"
    # A problem is "recently attempted" if it appears among the learner's last N attempts.
    recent_window: int = 3

    def recommend(
        self,
        index: AttemptRecord,
        history: Sequence[AttemptRecord],
        problems: Mapping[str, ProblemSpec],
        skill_maps: SkillMaps | None = None,
    ) -> Recommendation:
        """Choose the next activity after `index`.

        `history` is every diagnosed attempt by the learner (it may include `index`);
        `problems` is the catalogue, by slug; `skill_maps` holds the stored skill-map
        snapshot of each content version the attempts were diagnosed against.
        """
        spec = problems[index.problem_slug]
        attempts = sorted(
            {a.submission_id: a for a in (*history, index)}.values(), key=lambda a: a.created_at
        )
        recent = [a.problem_slug for a in attempts[-self.recent_window :]]
        family = sorted(
            (p for p in problems.values() if p.family == spec.family and p.recommendable),
            key=lambda p: p.slug,
        )
        base: dict[str, Any] = {
            "index_submission": index.submission_id,
            "index_outcome": index.outcome.value,
            "family": spec.family,
            "recent_problems": recent,
        }

        def make(rule: Rule, action: Action, slug: str | None, **kw: Any) -> Recommendation:
            rationale = {**base, **kw.pop("rationale", {})}
            return Recommendation(
                policy=self.name,
                policy_version=self.version,
                rule=rule,
                action=action,
                problem_slug=slug,
                rationale=rationale,
                **kw,
            )

        if index.outcome in (Outcome.COMPILE_ERROR, Outcome.EXECUTION_ERROR):
            return make(
                Rule.NOT_EVALUATED,
                Action.RETRY,
                spec.slug,
                rationale={"note": "No test evidence was produced; retry the same problem."},
            )
        if index.outcome in _ABSTAINED:
            return make(
                Rule.ABSTAINED,
                Action.RETRY,
                spec.slug,
                review_flag=True,
                rationale={
                    "note": "The diagnosis abstained, so no skill is targeted and no "
                    "improvement criterion is claimed. Flagged for researcher review."
                },
            )

        if index.outcome is Outcome.NON_TERMINATION_OBSERVED:
            return make(
                Rule.ABSTAINED,
                Action.RETRY,
                spec.slug,
                review_flag=True,
                rationale={
                    "note": "The program did not finish within the time limit on some tests. "
                    "That is a symptom many errors share, so no skill is targeted and no "
                    "improvement criterion is claimed (ADR-027). Flagged for researcher review."
                },
            )

        model_skill = {m.key: m.skill for m in spec.error_models}
        if index.outcome is Outcome.HYPOTHESIS_SUPPORTED:
            assert index.selected_model is not None  # noqa: S101 - invariant of the outcome
            skill = model_skill[index.selected_model]
            limitation = next(
                m.known_limitation for m in spec.error_models if m.key == index.selected_model
            )
            qualified = index.qualified or limitation is not None
            chosen, ranking = self._densest(family, {skill}, recent, spec)
            return make(
                Rule.HYPOTHESIS_SUPPORTED,
                _action(chosen, spec),
                chosen.slug,
                target_skills=(skill,),
                criterion=SuccessCriterion(
                    skills=(skill,),
                    excluded_model_skills=(skill,),
                    text=f"every reliable follow-up test probing {skill} passes, and the "
                    f"follow-up is not diagnosed with an error model of {skill}",
                ),
                rationale={
                    "selected_model": index.selected_model,
                    # Weak or colliding evidence: the follow-up targets the skill, and no
                    # wording may present the specific error as established.
                    "qualified_hypothesis": qualified,
                    **({"known_limitation": limitation} if limitation else {}),
                    "ranking": ranking,
                },
            )

        if index.outcome is Outcome.AMBIGUOUS:
            skills = {model_skill[c] for c in index.candidates}
            chosen, ranking = self._discriminating(family, skills, recent, spec)
            return make(
                Rule.AMBIGUOUS,
                _action(chosen, spec),
                chosen.slug,
                target_skills=tuple(sorted(skills)),
                criterion=SuccessCriterion(
                    skills=tuple(sorted(skills)),
                    text=f"every reliable follow-up test probing {', '.join(sorted(skills))} "
                    "passes",
                ),
                rationale={"candidates": list(index.candidates), "ranking": ranking},
            )

        # NO_FAILURE_OBSERVED: move to the least-evidenced problem not yet passed. No other
        # outcome may reach this branch: an outcome added without a rule is an error here,
        # never a pass.
        if index.outcome is not Outcome.NO_FAILURE_OBSERVED:
            raise ValueError(f"policy {self.version} has no rule for outcome {index.outcome}")
        passed = {a.problem_slug for a in attempts if a.outcome is Outcome.NO_FAILURE_OBSERVED}
        remaining = [p for p in family if p.slug not in passed]
        if not remaining:
            return make(
                Rule.NO_FAILURE_OBSERVED,
                Action.NONE,
                None,
                rationale={
                    "note": "Every recommendable problem in the family has an attempt with no "
                    "failure observed on its tests. That is not evidence of complete "
                    "understanding."
                },
            )
        ledger = build_ledger(attempts, problems, skill_maps)

        def evidence(p: ProblemSpec) -> int:
            return sum(reliable_count(ledger, s) for s in _skills(p))

        ranked = sorted(remaining, key=lambda p: (p.slug in recent, evidence(p), p.slug))
        chosen = ranked[0]
        all_skills = tuple(sorted(_skills(chosen)))
        return make(
            Rule.NO_FAILURE_OBSERVED,
            _action(chosen, spec),
            chosen.slug,
            target_skills=all_skills,
            criterion=SuccessCriterion(
                skills=all_skills, text="every reliable test of the follow-up problem passes"
            ),
            rationale={
                "ranking": [
                    {"problem": p.slug, "recent": p.slug in recent, "ledger_evidence": evidence(p)}
                    for p in ranked
                ]
            },
        )

    @staticmethod
    def _densest(
        family: list[ProblemSpec], skills: set[str], recent: list[str], fallback: ProblemSpec
    ) -> tuple[ProblemSpec, list[dict[str, Any]]]:
        """Prefer problems not recently attempted, then the most tests probing `skills`."""
        rows = [(p, len(tests_probing(p, skills))) for p in family]
        rows = [r for r in rows if r[1] > 0]
        rows.sort(key=lambda r: (r[0].slug in recent, -r[1], r[0].slug))
        chosen = rows[0][0] if rows else fallback  # no test probes the skill: retry
        return chosen, [
            {"problem": p.slug, "recent": p.slug in recent, "probing_tests": n} for p, n in rows
        ]

    @staticmethod
    def _discriminating(
        family: list[ProblemSpec], skills: set[str], recent: list[str], fallback: ProblemSpec
    ) -> tuple[ProblemSpec, list[dict[str, Any]]]:
        """Prefer problems with error models for more of the candidate skills.

        A problem can only tell candidate skills apart if it models errors of those skills;
        ties go to problems not recently attempted, then to more probing tests.
        """
        rows = [
            (
                p,
                len({m.skill for m in p.error_models} & skills),
                len(tests_probing(p, skills)),
            )
            for p in family
        ]
        rows = [r for r in rows if r[2] > 0]
        rows.sort(key=lambda r: (-r[1], r[0].slug in recent, -r[2], r[0].slug))
        chosen = rows[0][0] if rows else fallback
        return chosen, [
            {
                "problem": p.slug,
                "modelled_skills": m,
                "recent": p.slug in recent,
                "probing_tests": n,
            }
            for p, m, n in rows
        ]


def _skills(spec: ProblemSpec) -> set[str]:
    return {s for t in spec.tests for s in spec.skills_probed_by(t)}


def _action(chosen: ProblemSpec, index: ProblemSpec) -> Action:
    return Action.RETRY if chosen.slug == index.slug else Action.NEW_PROBLEM
