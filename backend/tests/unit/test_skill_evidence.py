"""Skill-evidence contract (docs/component-interfaces.md §5; ADR-023 D2-D4)."""

from __future__ import annotations

from codeadapt.adaptation import SkillMap, TestStatus, build_ledger, skill_observations
from codeadapt.diagnosis import Outcome
from tests.unit.test_adaptation import LB_EQUALITY, PROBLEMS, attempt

LB = PROBLEMS["lower-bound"]
E2_TESTS = ("above_all", "single_above", "large_above_all")


def failures(ledger: dict) -> dict[str, list[str]]:  # type: ignore[type-arg]
    return {
        skill: [e.test_key for e in items if e.status is TestStatus.FAILED]
        for skill, items in ledger.items()
        if any(e.status is TestStatus.FAILED for e in items)
    }


# --------------------------------------------------------------- D2: ledger policy 1.2
def test_qualified_diagnosis_adds_no_failure_evidence() -> None:
    weak = attempt(
        "lower-bound",
        Outcome.HYPOTHESIS_SUPPORTED,
        model="hi_init_last_index",
        failing=E2_TESTS,
        qualified=True,
    )
    assert failures(build_ledger([weak], PROBLEMS)) == {}
    assert not [o for o in skill_observations([weak], PROBLEMS) if o.value == "incorrect"]


def test_documented_collision_adds_no_failure_evidence_even_if_unqualified() -> None:
    # hi_init_last_index documents a collision (`known_limitation`); that alone is enough.
    stale = attempt(
        "lower-bound", Outcome.HYPOTHESIS_SUPPORTED, model="hi_init_last_index", failing=E2_TESTS
    )
    assert failures(build_ledger([stale], PROBLEMS)) == {}


def test_unqualified_diagnosis_still_counts_for_its_models_skill_only() -> None:
    assert failures(build_ledger([LB_EQUALITY], PROBLEMS)) == {
        "equality_handling": ["duplicates_middle", "duplicates_all"]
    }


# --------------------------------------------------------------- D3: one per attempt+skill
def test_one_observation_per_attempt_and_skill() -> None:
    obs = skill_observations([LB_EQUALITY], PROBLEMS)
    assert {(o.skill, o.value) for o in obs} == {
        ("equality_handling", "incorrect"),
        ("search_space_boundaries", "correct"),
        ("loop_termination", "correct"),
        ("problem_specification", "correct"),
    }
    # Two failing tests, one behaviour pattern: a single incorrect observation.
    wrong = next(o for o in obs if o.value == "incorrect")
    assert wrong.test_keys == ("duplicates_all", "duplicates_middle")
    assert wrong.basis == "supported diagnosis: stops_at_first_match"
    assert all(o.attempt_ordinal == 1 for o in obs)


def test_abstentions_give_no_incorrect_and_no_correct_for_touched_skills() -> None:
    for outcome in (Outcome.AMBIGUOUS, Outcome.UNMODELLED_BEHAVIOUR, Outcome.INSUFFICIENT_EVIDENCE):
        a = attempt("lower-bound", outcome, failing=("equal_first",))
        obs = {(o.skill, o.value) for o in skill_observations([a], PROBLEMS)}
        assert not any(v == "incorrect" for _, v in obs), outcome
        # equal_first probes equality, so equality gets nothing; untouched skills may pass.
        assert ("equality_handling", "correct") not in obs
        assert ("loop_termination", "correct") in obs


def test_no_skill_evidence_from_errors_or_unreliable_attempts() -> None:
    for outcome in (Outcome.COMPILE_ERROR, Outcome.EXECUTION_ERROR, Outcome.UNRELIABLE_EVIDENCE):
        assert skill_observations([attempt("lower-bound", outcome)], PROBLEMS) == ()


def test_an_excluded_test_withholds_its_skills() -> None:
    a = attempt("lower-bound", Outcome.NO_FAILURE_OBSERVED, excluded=("two_between",))
    skills = {o.skill for o in skill_observations([a], PROBLEMS)}
    # two_between probes loop termination and specification.
    assert skills == {"search_space_boundaries", "equality_handling"}


def test_retries_carry_their_ordinal() -> None:
    first = attempt("lower-bound", Outcome.NO_FAILURE_OBSERVED, n=0)
    again = attempt("lower-bound", Outcome.NO_FAILURE_OBSERVED, n=1)
    other = attempt("count-occurrences", Outcome.NO_FAILURE_OBSERVED, n=2)
    obs = skill_observations([first, again, other], PROBLEMS)
    assert {o.attempt_ordinal for o in obs if o.submission_id == "s1"} == {2}
    assert {o.attempt_ordinal for o in obs if o.submission_id == "s2"} == {1}


# --------------------------------------------------------------- D4: version identity
def test_attempts_use_their_own_versions_skill_map() -> None:
    # An older version where duplicates_middle was mapped to a different skill.
    old = SkillMap.from_spec(LB, "old")
    old = old.model_copy(
        update={"test_skills": {**old.test_skills, "duplicates_middle": ("loop_termination",)}}
    )
    a = attempt("lower-bound", Outcome.NO_FAILURE_OBSERVED).model_copy(
        update={"problem_version": "old"}
    )
    ledger = build_ledger([a], PROBLEMS, {"old": old})
    loop = {e.test_key for e in ledger["loop_termination"]}
    assert "duplicates_middle" in loop
    assert "duplicates_middle" not in {e.test_key for e in ledger["equality_handling"]}


def test_a_version_without_a_snapshot_contributes_nothing() -> None:
    a = LB_EQUALITY.model_copy(update={"problem_version": "unknown"})
    assert build_ledger([a], PROBLEMS, {}) == {}
    assert skill_observations([a], PROBLEMS, {}) == ()


def test_stored_snapshot_round_trips_and_rejects_unknown_formats() -> None:
    smap = SkillMap.from_spec(LB, "v1")
    assert SkillMap.from_stored(smap.model_dump(mode="json")) == smap
    assert SkillMap.from_stored({**smap.model_dump(mode="json"), "format": 99}) is None
    assert SkillMap.from_stored(None) is None
    # upper_bound_confusion since L20 S1 for the original problems (case O1, 2026-10-26).
    assert smap.documented_collisions == ("hi_init_last_index", "upper_bound_confusion")


def test_catalogue_sync_writes_and_backfills_snapshots(sessions) -> None:  # type: ignore[no-untyped-def]
    from sqlalchemy import select

    from codeadapt.content.catalogue import Catalogue
    from codeadapt.db.models import ProblemVersion
    from tests.paths import DEMO_CONTENT

    catalogue = Catalogue.load(DEMO_CONTENT)
    lb = catalogue.by_slug["lower-bound"]
    with sessions() as session:
        # A row registered before snapshots existed, and a retired version.
        session.add(ProblemVersion(version=lb.version, slug="lower-bound", family="f", title="t"))
        session.add(ProblemVersion(version="retired", slug="lower-bound", family="f", title="t"))
        session.commit()
        catalogue.sync(session)
        rows = {r.version: r for r in session.scalars(select(ProblemVersion))}
    assert SkillMap.from_stored(rows[lb.version].skill_map) == SkillMap.from_spec(
        lb.spec, lb.version
    )
    assert rows["retired"].skill_map is None
    assert all(rows[p.version].skill_map for p in catalogue.problems)
