"""Consumers of `non_termination_observed` (ADR-027): a symptom, never a named error.

The outcome must not produce an `incorrect` skill observation, a skill-specific
recommendation, a hint or a diagnosis count, and it must never reach the no-failure branch
of the policy.
"""

from __future__ import annotations

from enum import StrEnum

import pytest

from codeadapt.adaptation import (
    Action,
    AttemptRecord,
    PolicyV1,
    Rule,
    Verdict,
    evaluate_followup,
    skill_observations,
)
from codeadapt.api.feedback import feedback_view
from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import DiagnosisRow
from codeadapt.diagnosis import Outcome
from codeadapt.evaluation.metrics import CaseResult, compute
from codeadapt.learner.bkt import NOT_EVALUATED, counted_attempts
from tests.paths import DEMO_CONTENT
from tests.unit.test_adaptation import LB_EQUALITY, POLICY, PROBLEMS, attempt

NT = Outcome.NON_TERMINATION_OBSERVED
LB = PROBLEMS["lower-bound"]
LOOP_TESTS = tuple(t.key for t in LB.tests if "loop_termination" in LB.skills_probed_by(t))


def timed_out(n: int = 0, slug: str = "lower-bound") -> AttemptRecord:
    spec = PROBLEMS[slug]
    failing = tuple(t.key for t in spec.tests if "loop_termination" in spec.skills_probed_by(t))
    return attempt(slug, NT, n=n, failing=failing)


# ---------------------------------------------------------------- policy v1.4 (P1)
def test_non_termination_retries_the_same_problem_without_a_skill_or_criterion() -> None:
    index = timed_out()
    rec = POLICY.recommend(index, [index], PROBLEMS)
    assert (rec.rule, rec.action, rec.problem_slug) == (Rule.ABSTAINED, Action.RETRY, "lower-bound")
    assert rec.target_skills == ()
    assert rec.criterion is None
    assert rec.review_flag
    assert "ADR-027" in rec.rationale["note"]
    assert rec.policy_version == "1.5"
    # Policy 1.5 changed only the follow-up ranking; this rule is the same in 1.4.
    old = PolicyV1(version="1.4").recommend(index, [index], PROBLEMS)
    assert old.model_dump(exclude={"policy_version"}) == rec.model_dump(exclude={"policy_version"})


@pytest.mark.parametrize("outcome", list(Outcome))
def test_every_outcome_has_an_explicit_rule(outcome: Outcome) -> None:
    index = attempt(
        "lower-bound",
        outcome,
        model="upper_bound_confusion" if outcome is Outcome.HYPOTHESIS_SUPPORTED else None,
        candidates=("upper_bound_confusion", "returns_wrong_pointer")
        if outcome is Outcome.AMBIGUOUS
        else (),
        failing=() if outcome is Outcome.NO_FAILURE_OBSERVED else ("empty",),
    )
    rec = POLICY.recommend(index, [index], PROBLEMS)
    # Only a no-failure attempt may be treated as a pass.
    assert (rec.rule is Rule.NO_FAILURE_OBSERVED) == (outcome is Outcome.NO_FAILURE_OBSERVED)


class _FutureOutcome(StrEnum):
    SOMETHING_NEW = "something_new"


def test_an_outcome_without_a_rule_is_an_error_not_a_pass() -> None:
    # Simulates an outcome added later without a policy rule.
    unknown = timed_out().model_construct(
        **{**dict(timed_out()), "outcome": _FutureOutcome.SOMETHING_NEW}
    )
    with pytest.raises(ValueError, match="has no rule"):
        POLICY.recommend(unknown, [], PROBLEMS)


# ---------------------------------------------------------------- skill evidence and BKT
def test_non_termination_adds_no_incorrect_observation() -> None:
    obs = skill_observations([timed_out()], PROBLEMS)
    assert not [o for o in obs if o.value == "incorrect"]
    # The skill the timed-out tests probe gets nothing from this attempt ...
    assert "loop_termination" not in {o.skill for o in obs}
    # ... and a skill whose every probing test passed still gets its correct observation
    # (ledger rule C, unchanged).
    passed_skills = {
        s
        for s in {s for t in LB.tests for s in LB.skills_probed_by(t)}
        if all(t.key not in LOOP_TESTS for t in LB.tests if s in LB.skills_probed_by(t))
    }
    assert {o.skill for o in obs} == passed_skills
    assert all(o.value == "correct" for o in obs)


def test_v1_1_termination_diagnosis_did_add_an_incorrect_observation() -> None:
    # The contrast ADR-027 removes: the same tests named as no_progress_update, unqualified.
    named = attempt(
        "lower-bound", Outcome.HYPOTHESIS_SUPPORTED, model="no_progress_update", failing=LOOP_TESTS
    )
    obs = skill_observations([named], PROBLEMS)
    assert ("loop_termination", "incorrect") in {(o.skill, o.value) for o in obs}


def test_non_termination_consumes_the_counted_opportunity_without_failure_evidence() -> None:
    # LM1 rule: execution was reliable and feedback was delivered.
    assert NT not in NOT_EVALUATED
    first, retry = timed_out(n=0), LB_EQUALITY.model_copy(update={"submission_id": "s1"})
    retry = retry.model_copy(update={"created_at": first.created_at.replace(minute=5)})
    assert counted_attempts([first, retry]) == {"s0"}


# ---------------------------------------------------------------- follow-up evaluation
def test_follow_up_that_times_out_on_targeted_probes_does_not_meet_the_criterion() -> None:
    rec = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    assert rec.problem_slug is not None
    spec = PROBLEMS[rec.problem_slug]
    targeted = tuple(t.key for t in spec.tests if "equality_handling" in spec.skills_probed_by(t))
    follow = attempt(rec.problem_slug, NT, n=5, failing=targeted[:1])
    ev = evaluate_followup(rec, LB_EQUALITY, LB, follow, spec)
    assert ev.verdict is Verdict.CRITERION_NOT_MET


def test_retry_after_non_termination_claims_nothing() -> None:
    index = timed_out()
    rec = POLICY.recommend(index, [index], PROBLEMS)
    follow = attempt("lower-bound", Outcome.NO_FAILURE_OBSERVED, n=6)
    assert evaluate_followup(rec, index, LB, follow, LB).verdict is Verdict.NOT_COMPARABLE


# ---------------------------------------------------------------- student feedback
def test_feedback_names_the_symptom_without_a_hint_or_model() -> None:
    problem = Catalogue.load(DEMO_CONTENT).by_slug["lower-bound"]
    row = DiagnosisRow(
        outcome=NT.value,
        selected_model=None,
        rationale={
            "timed_out_tests": ["large_absent"],
            "consistent_models": ["no_progress_update"],
        },
    )
    view = feedback_view(problem, row, [])
    assert view.hint is None
    assert "did not finish within the time limit" in view.message
    assert "far too slow" in view.message
    for model in problem.spec.error_models:
        assert model.key not in view.message


# ---------------------------------------------------------------- evaluation metrics
def test_a_symptom_is_neither_a_true_nor_a_false_diagnosis() -> None:
    case = CaseResult(
        problem="lower-bound",
        file="x.cpp",
        truth="no_progress_update",
        outcomes=(NT, NT),
        selected_models=(None, None),
        candidates=(),
        signatures=(("time_limit",), ("time_limit",)),
    )
    assert case.classification == "symptom_reported"
    m = compute([case], {"no_progress_update"})
    assert (m.coverage.numerator, m.false_positive_diagnoses) == (0, 0)
    assert m.abstentions_by_outcome == {"non_termination_observed": 1}
