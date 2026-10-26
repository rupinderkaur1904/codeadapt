"""LM1: standard BKT over skill observations (ADR-025).

These tests check the implementation against hand-calculated values and the owner's
rules (2026-10-17). They are not evidence that the estimates describe real learners: the
parameters are assumptions and the attempts here are synthetic.
"""

from __future__ import annotations

import random
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from codeadapt.adaptation import AttemptRecord, SkillMap
from codeadapt.diagnosis import Outcome
from codeadapt.learner import ASSUMED_PARAMS_1, BktParams, estimate, posterior, update
from codeadapt.learner.bkt import LABEL, RETRY_REASON
from tests.unit.test_adaptation import LB_EQUALITY, PROBLEMS, attempt

P = ASSUMED_PARAMS_1  # P(L0)=0.3, P(T)=0.1, P(G)=0.2, P(S)=0.1
EQ = "equality_handling"


def at(a: AttemptRecord, n: int, version: str | None = None) -> AttemptRecord:
    return a.model_copy(
        update={
            "submission_id": f"s{n}",
            "created_at": a.created_at + timedelta(minutes=n),
            "problem_version": version,
        }
    )


def passing(slug: str, n: int, version: str | None = None) -> AttemptRecord:
    return at(attempt(slug, Outcome.NO_FAILURE_OBSERVED), n, version)


def skill(attempts: list[AttemptRecord], name: str = EQ, **kw):  # type: ignore[no-untyped-def]
    return next(s for s in estimate(attempts, PROBLEMS, **kw).skills if s.skill == name)


# ------------------------------------------------------------------- arithmetic
def test_update_matches_hand_calculation_for_a_correct_observation() -> None:
    # posterior = 0.3*0.9 / (0.3*0.9 + 0.7*0.2) = 27/41; then + (14/41)*0.1 = 28.4/41
    assert posterior(0.3, True, P) == pytest.approx(27 / 41)
    assert update(0.3, True, P) == pytest.approx(28.4 / 41)  # 0.692683


def test_update_matches_hand_calculation_for_an_incorrect_observation() -> None:
    # posterior = 0.3*0.1 / (0.3*0.1 + 0.7*0.8) = 3/59; then + (56/59)*0.1 = 8.6/59
    assert posterior(0.3, False, P) == pytest.approx(3 / 59)
    assert update(0.3, False, P) == pytest.approx(8.6 / 59)  # 0.145763


def test_two_step_sequence_matches_hand_calculation() -> None:
    p1 = 28.4 / 41
    # incorrect from p1: p1*0.1 / (p1*0.1 + (1-p1)*0.8), then the learn transition
    post = p1 * 0.1 / (p1 * 0.1 + (1 - p1) * 0.8)
    assert update(update(0.3, True, P), False, P) == pytest.approx(post + (1 - post) * 0.1)
    assert update(update(0.3, True, P), False, P) == pytest.approx(0.297833, abs=1e-6)


def test_direction_of_each_observation_before_the_transition() -> None:
    for p in [i / 20 for i in range(1, 20)]:
        assert posterior(p, True, P) >= p
        assert posterior(p, False, P) <= p
        assert 0 < update(p, True, P) < 1
        assert 0 < update(p, False, P) < 1


@pytest.mark.parametrize(
    ("field", "value"),
    [("p_init", 0.0), ("p_learn", 1.0), ("p_guess", 0.5), ("p_slip", 0.6), ("p_init", -0.1)],
)
def test_parameter_constraints_are_enforced(field: str, value: float) -> None:
    good = P.model_dump()
    with pytest.raises(ValidationError):
        BktParams(**{**good, field: value})


def test_parameter_set_is_named_and_labelled_as_an_assumption() -> None:
    result = estimate([], PROBLEMS)
    assert result.parameter_set == "bkt-params-assumed-1"
    assert result.label == LABEL == "estimated under assumed parameters"
    assert any("not fitted" in a for a in result.assumptions)
    for assumption in ("skills are independent", "no forgetting", "same parameters"):
        assert any(assumption in a for a in result.assumptions)


# ------------------------------------------------------------------- counting (L1)
def test_first_reliable_attempt_per_problem_version_counts_and_retries_do_not() -> None:
    history = [
        at(LB_EQUALITY, 0),
        passing("lower-bound", 1),  # retry on the same problem version
        passing("count-occurrences", 2),
        passing("last-less-than", 3),
    ]
    eq = skill(history)
    assert [(t.observation.submission_id, t.counted) for t in eq.observations] == [
        ("s0", True),
        ("s1", False),
        ("s2", True),
        ("s3", True),
    ]
    retry = eq.observations[1]
    assert retry.reason == RETRY_REASON and retry.p_known_after is None
    expected = update(update(update(0.3, False, P), True, P), True, P)
    assert eq.state == "estimated"
    assert eq.p_known == pytest.approx(expected)
    assert eq.observations[-1].p_known_after == pytest.approx(expected)


# Owner rule (2026-10-17): a first attempt whose execution was reliable and whose feedback
# was delivered uses up the counted opportunity even when it yields no skill observation;
# an inconclusive or otherwise unreliable execution does not.
@pytest.mark.parametrize(
    "first",
    [
        attempt("lower-bound", Outcome.AMBIGUOUS, failing=("equal_first",)),
        attempt("lower-bound", Outcome.UNMODELLED_BEHAVIOUR, failing=("equal_first",)),
        attempt("lower-bound", Outcome.INSUFFICIENT_EVIDENCE, failing=("equal_first",)),
        attempt(
            "lower-bound",
            Outcome.HYPOTHESIS_SUPPORTED,
            model="hi_init_last_index",
            failing=("above_all", "single_above", "large_above_all"),
            qualified=True,
        ),
    ],
    ids=["ambiguous", "unmodelled", "insufficient", "qualified"],
)
def test_a_reliable_abstaining_first_attempt_uses_up_the_counted_attempt(
    first: AttemptRecord,
) -> None:
    eq = skill([at(first, 0), passing("lower-bound", 1)])
    # Whatever the first attempt said about equality (nothing, for the abstentions), the
    # retry's observation is listed but not counted.
    retry = next(t for t in eq.observations if t.observation.submission_id == "s1")
    assert not retry.counted and retry.reason == RETRY_REASON
    assert all(t.observation.value != "incorrect" for t in eq.observations)


@pytest.mark.parametrize(
    "outcome", [Outcome.UNRELIABLE_EVIDENCE, Outcome.EXECUTION_ERROR, Outcome.COMPILE_ERROR]
)
def test_attempts_not_reliably_evaluated_do_not_use_up_the_counted_attempt(
    outcome: Outcome,
) -> None:
    eq = skill([at(attempt("lower-bound", outcome), 0), passing("lower-bound", 1)])
    assert [(t.observation.submission_id, t.counted) for t in eq.observations] == [("s1", True)]


def test_an_attempt_made_unreliable_by_inconclusive_runs_does_not_use_it_up() -> None:
    # Every test stopped by the wall clock twice (ADR-023 D1): excluded, so the diagnosis
    # is unreliable_evidence and the next attempt is still the counted one.
    keys = tuple(t.key for t in PROBLEMS["lower-bound"].tests)
    stalled = at(attempt("lower-bound", Outcome.UNRELIABLE_EVIDENCE, excluded=keys), 0)
    eq = skill([stalled, at(LB_EQUALITY, 1)])
    assert [(t.observation.submission_id, t.counted) for t in eq.observations] == [("s1", True)]
    assert eq.observations[0].observation.value == "incorrect"


def test_a_reliable_attempt_with_some_inconclusive_tests_still_uses_it_up() -> None:
    # The attempt as a whole was evaluated and its feedback delivered; only the excluded
    # tests' skills lack an observation. The next attempt is a retry.
    partial = at(attempt("lower-bound", Outcome.NO_FAILURE_OBSERVED, excluded=("equal_first",)), 0)
    eq = skill([partial, passing("lower-bound", 1)])
    assert [(t.observation.submission_id, t.counted) for t in eq.observations] == [("s1", False)]


# ------------------------------------------------------------------- excluded evidence
def test_excluded_evidence_never_changes_an_estimate() -> None:
    base = [at(LB_EQUALITY, 0), passing("count-occurrences", 2), passing("last-less-than", 3)]
    noise = [
        # an attempt whose evidence was unreliable as a whole (e.g. inconclusive runs)
        at(attempt("count-occurrences", Outcome.UNRELIABLE_EVIDENCE), 1),
        # a qualified diagnosis: shown to the student, but no failure evidence
        at(
            attempt(
                "last-less-than",
                Outcome.HYPOTHESIS_SUPPORTED,
                model="hi_init_last_index",
                failing=("equal_first",),
                qualified=True,
            ),
            4,
        ),
        at(attempt("lower-bound", Outcome.COMPILE_ERROR), 5),
    ]
    clean, noisy = skill(base), skill(base + noise)
    assert noisy.p_known == clean.p_known
    assert noisy.counted == clean.counted
    assert not any(t.observation.value == "incorrect" for t in noisy.observations[1:])


# ------------------------------------------------------------------- determinism
def test_recomputation_is_deterministic_and_independent_of_input_order() -> None:
    history = [
        at(LB_EQUALITY, 0),
        passing("lower-bound", 1),
        passing("count-occurrences", 2),
        passing("last-less-than", 3),
    ]
    first = estimate(history, PROBLEMS)
    shuffled = history[:]
    random.Random(7).shuffle(shuffled)  # noqa: S311 - test ordering only
    assert estimate(history, PROBLEMS) == first
    assert estimate(shuffled, PROBLEMS) == first


# ------------------------------------------------------------------- version identity
def test_versions_keep_provenance_but_count_as_one_problem() -> None:
    lb = PROBLEMS["lower-bound"]
    maps = {v: SkillMap.from_spec(lb, v) for v in ("lb-v1", "lb-v2", "lb-v3")}
    history = [
        at(LB_EQUALITY, 0, "lb-v1"),
        passing("lower-bound", 1, "lb-v1"),  # retry on v1
        passing("lower-bound", 2, "lb-v2"),  # first attempt on v2: counted
        passing("lower-bound", 3, "lb-v3"),  # first attempt on v3: counted
    ]
    eq = skill(history, skill_maps=maps)
    assert [(t.observation.problem_version, t.counted) for t in eq.observations] == [
        ("lb-v1", True),
        ("lb-v1", False),
        ("lb-v2", True),
        ("lb-v3", True),
    ]
    # Three counted observations, one underlying problem: below the display threshold.
    assert eq.counted == 3 and eq.distinct_problems == 1
    assert eq.state == "insufficient_data" and eq.p_known is None


def test_a_version_without_a_snapshot_contributes_nothing() -> None:
    result = estimate([at(LB_EQUALITY, 0, "unknown-version")], PROBLEMS, skill_maps={})
    assert result.skills == ()


# ------------------------------------------------------------------- display threshold
def test_display_threshold_needs_three_counted_observations_from_two_problems() -> None:
    two = skill([at(LB_EQUALITY, 0), passing("count-occurrences", 1)])
    assert (two.counted, two.distinct_problems, two.state) == (2, 2, "insufficient_data")
    assert two.p_known is None
    # The trajectory is still traced for researchers below the threshold.
    assert two.observations[-1].p_known_after == pytest.approx(
        update(update(0.3, False, P), True, P)
    )
    three = skill(
        [at(LB_EQUALITY, 0), passing("count-occurrences", 1), passing("last-less-than", 2)]
    )
    assert (three.counted, three.distinct_problems, three.state) == (3, 3, "estimated")


# ------------------------------------------------------------------- isolation
def test_no_policy_or_student_code_reads_the_learner_model() -> None:
    src = Path(__file__).parents[2] / "src" / "codeadapt"
    readers = {
        p.relative_to(src).as_posix()
        for p in src.rglob("*.py")
        if "codeadapt.learner" in p.read_text() and "learner" not in p.parts
    }
    assert readers == {"api/app.py", "api/schemas.py"}
    app = (src / "api" / "app.py").read_text()
    # The only route that calls it is the researcher-only one.
    assert app.count("estimate(") == 1
    assert '"/api/v1/research/learner-model"' in app


# ------------------------------------------------------------------- CE1.1 (decision E2)
def test_a_non_recommendable_problem_still_feeds_the_learner_model() -> None:
    # first-true was excluded from policy v1's candidates when this was written (E2); it is
    # recommendable since 2026-10-26. Either way the flag never touches skill evidence: the
    # estimate is the same with first-true switched off.
    hidden = {
        **PROBLEMS,
        "first-true": PROBLEMS["first-true"].model_copy(update={"recommendable": False}),
    }
    ft = at(
        attempt(
            "first-true",
            Outcome.HYPOTHESIS_SUPPORTED,
            model="hi_skips_candidate",
            failing=("sample_interior", "two_false_true", "second_index", "last_index"),
        ),
        0,
    )
    history = [ft, passing("lower-bound", 1), passing("count-occurrences", 2)]
    b = skill(history, "search_space_boundaries")
    first = b.observations[0]
    assert (first.observation.problem_slug, first.observation.value, first.counted) == (
        "first-true",
        "incorrect",
        True,
    )
    assert (b.counted, b.distinct_problems, b.state) == (3, 3, "estimated")
    assert estimate(history, hidden) == estimate(history, PROBLEMS)
