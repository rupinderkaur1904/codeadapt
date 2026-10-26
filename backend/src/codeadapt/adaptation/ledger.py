"""The learner evidence ledger: per skill, the chronological probe observations.

There is deliberately no latent "mastery" variable (methodology §5): the ledger is a
reorganisation of stored evidence, nothing more.

A failing test is evidence of a behavioural difference, not of a skill. So a failure enters
the ledger only when a supported diagnosis explains it, and then only under the diagnosed
model's skill (ADR-019, change C5). Since policy 1.2 (ADR-023, D2) the diagnosis must also
be unqualified: a diagnosis resting on one behaviour group, or on a model with a documented
collision, is still shown to the student as a qualified hint but adds no failure evidence.
Failures in ambiguous, unmodelled, insufficient, unreliable or qualified attempts stay in
the stored submission but are not skill evidence.

Attempts are attributed with the skill map of their own content version (D4).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from codeadapt.adaptation.models import (
    AttemptRecord,
    ProbeEvidence,
    ProbeResult,
    SkillObservation,
    TestStatus,
)
from codeadapt.adaptation.skillmap import SkillMap, current_skill_maps
from codeadapt.content.models import ProblemSpec
from codeadapt.diagnosis.models import Outcome

Ledger = dict[str, tuple[ProbeEvidence, ...]]
SkillMaps = Mapping[str, SkillMap]

# Attempts that ran nothing usable, or whose evidence was unreliable as a whole.
_NO_SKILL_EVIDENCE = {Outcome.COMPILE_ERROR, Outcome.EXECUTION_ERROR, Outcome.UNRELIABLE_EVIDENCE}


def skill_map_for(
    attempt: AttemptRecord,
    problems: Mapping[str, ProblemSpec],
    skill_maps: SkillMaps | None = None,
) -> SkillMap | None:
    """The snapshot to attribute `attempt` with, or None if it must contribute nothing.

    A stored attempt carries its content version and resolves only through that version's
    snapshot. An attempt without a version (synthetic trajectories) uses the current spec.
    """
    if attempt.problem_version is not None:
        return (skill_maps or {}).get(attempt.problem_version)
    return current_skill_maps(problems).get(attempt.problem_slug)


def explaining_model(attempt: AttemptRecord, smap: SkillMap) -> str | None:
    """The model whose diagnosis may count as failure evidence (policy 1.2), if any."""
    model = attempt.selected_model
    if (
        attempt.outcome is not Outcome.HYPOTHESIS_SUPPORTED
        or model is None
        or model not in smap.model_skills
        or attempt.qualified
        or model in smap.documented_collisions
    ):
        return None
    return model


def build_ledger(
    attempts: Sequence[AttemptRecord],
    problems: Mapping[str, ProblemSpec],
    skill_maps: SkillMaps | None = None,
) -> Ledger:
    """Attribute recorded test outcomes to skills.

    Passed and excluded tests go to the skills their probes name (excluded ones stay
    visible but are not counted). A failed test goes only to the skill of the error model
    an unqualified supported diagnosis selected; with a supported diagnosis, strict
    consistency means the model predicts every reliable failure. Other failures are left
    out. Test keys the snapshot does not define are skipped rather than guessed.
    """
    entries: dict[str, list[ProbeEvidence]] = {}
    for attempt in sorted(attempts, key=lambda a: a.created_at):
        smap = skill_map_for(attempt, problems, skill_maps)
        if smap is None:
            continue
        explaining = explaining_model(attempt, smap)
        for key, status in attempt.tests.items():
            if key not in smap.test_skills:
                continue
            if status is TestStatus.FAILED:
                if explaining is None:
                    continue
                skills: tuple[str, ...] = (smap.model_skills[explaining],)
            else:
                skills = smap.skills_of(key)
            for skill in skills:
                entries.setdefault(skill, []).append(
                    ProbeEvidence(
                        skill=skill,
                        problem_slug=attempt.problem_slug,
                        test_key=key,
                        submission_id=attempt.submission_id,
                        status=status,
                        explained_by=explaining if status is TestStatus.FAILED else None,
                    )
                )
    return {skill: tuple(items) for skill, items in entries.items()}


def skill_observations(
    attempts: Sequence[AttemptRecord],
    problems: Mapping[str, ProblemSpec],
    skill_maps: SkillMaps | None = None,
) -> tuple[SkillObservation, ...]:
    """At most one observation per (attempt, skill): the learner-model input (D3).

    * `incorrect` for the skill of the model an unqualified supported diagnosis selected.
    * `correct` for any other skill when at least one test probes it, every test probing
      it passed, and none was failed or excluded (rule C).
    * Nothing otherwise, and nothing at all from compile errors, execution errors,
      unreliable evidence, attempts without a skill map, or attempts whose source names a
      library call the statement forbids (D1, ADR-035). Such an attempt still exists, is
      still diagnosed and still takes its place in the attempt order.

    Counting per attempt rather than per test keeps tests that exercise the same behaviour
    from becoming independent pieces of evidence.
    """
    out: list[SkillObservation] = []
    ordinal: dict[str, int] = {}
    for attempt in sorted(attempts, key=lambda a: a.created_at):
        smap = skill_map_for(attempt, problems, skill_maps)
        ordinal[attempt.problem_slug] = ordinal.get(attempt.problem_slug, 0) + 1
        if smap is None or attempt.outcome in _NO_SKILL_EVIDENCE:
            continue
        if attempt.banned_names_found:
            continue
        explaining = explaining_model(attempt, smap)
        weak_skill = smap.model_skills[explaining] if explaining is not None else None
        by_skill: dict[str, list[tuple[str, TestStatus]]] = {}
        for test_key, status in attempt.tests.items():
            for skill in smap.skills_of(test_key):
                by_skill.setdefault(skill, []).append((test_key, status))
        if weak_skill is not None:
            by_skill.setdefault(weak_skill, [])
        for skill in sorted(by_skill):
            tests = sorted(by_skill[skill])
            if skill == weak_skill:
                value, basis = "incorrect", f"supported diagnosis: {explaining}"
                keys = tuple(sorted(k for k, s in attempt.tests.items() if s is TestStatus.FAILED))
            elif tests and all(s is TestStatus.PASSED for _, s in tests):
                value, basis = "correct", "every reliable test probing the skill passed"
                keys = tuple(k for k, _ in tests)
            else:
                continue
            out.append(
                SkillObservation(
                    skill=skill,
                    value=value,
                    basis=basis,
                    submission_id=attempt.submission_id,
                    problem_slug=attempt.problem_slug,
                    problem_version=attempt.problem_version,
                    created_at=attempt.created_at,
                    test_keys=keys,
                    attempt_ordinal=ordinal[attempt.problem_slug],
                )
            )
    return tuple(out)


def reliable_count(ledger: Ledger, skill: str) -> int:
    return sum(1 for e in ledger.get(skill, ()) if e.status is not TestStatus.EXCLUDED)


def tests_probing(spec: ProblemSpec, skills: set[str] | frozenset[str]) -> list[str]:
    return [t.key for t in spec.tests if spec.skills_probed_by(t) & skills]


def probe_result(
    attempt: AttemptRecord | None, spec: ProblemSpec | None, probe: str
) -> ProbeResult:
    """Aggregate an attempt's outcomes over the tests carrying `probe`."""
    if attempt is None or spec is None or probe not in spec.probes:
        return ProbeResult.NOT_PROBED
    statuses = [
        attempt.tests[t.key] for t in spec.tests if probe in t.probes and t.key in attempt.tests
    ]
    if not statuses:
        return ProbeResult.NOT_PROBED
    if TestStatus.FAILED in statuses:
        return ProbeResult.FAILED
    if TestStatus.PASSED in statuses:
        return ProbeResult.PASSED
    return ProbeResult.EXCLUDED
