"""Policy v1 and follow-up evaluation over the demo content (methodology §5)."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from codeadapt.adaptation import (
    Action,
    AttemptRecord,
    Ledger,
    PolicyV1,
    ProbeResult,
    Relation,
    Rule,
    TestStatus,
    Verdict,
    build_ledger,
    evaluate_followup,
)
from codeadapt.content import load_catalogue
from codeadapt.content.models import ProblemSpec
from codeadapt.diagnosis import Outcome
from tests.paths import DEMO_CONTENT
from tests.unit.policy_cases import ORIGINAL, attempts_for, histories, recommendations, record

PROBLEMS: dict[str, ProblemSpec] = {p.spec.slug: p.spec for p in load_catalogue(DEMO_CONTENT)}
T0 = datetime(2026, 1, 1, tzinfo=UTC)
POLICY = PolicyV1()
# The catalogue as it was until 2026-10-26, when only the three original problems were
# recommendable (CE1 decision E2). The rule tests marked below pin policy 1.4 on it, as they
# were written; policy 1.5 and the current eligibility have their own tests
# (test_policy_1_5.py, test_recommendability.py).
E2_PROBLEMS = {
    s: p.model_copy(update={"recommendable": s in ORIGINAL}) for s, p in PROBLEMS.items()
}
POLICY_1_4 = PolicyV1(version="1.4")


def attempt(
    slug: str,
    outcome: Outcome,
    *,
    n: int = 0,
    model: str | None = None,
    candidates: tuple[str, ...] = (),
    qualified: bool = False,
    failing: tuple[str, ...] = (),
    excluded: tuple[str, ...] = (),
) -> AttemptRecord:
    tests: dict[str, TestStatus] = {}
    if outcome not in (Outcome.COMPILE_ERROR, Outcome.EXECUTION_ERROR):
        for t in PROBLEMS[slug].tests:
            tests[t.key] = (
                TestStatus.EXCLUDED
                if t.key in excluded
                else TestStatus.FAILED
                if t.key in failing
                else TestStatus.PASSED
            )
    return AttemptRecord(
        submission_id=f"s{n}",
        problem_slug=slug,
        created_at=T0 + timedelta(minutes=n),
        outcome=outcome,
        selected_model=model,
        candidates=candidates or ((model,) if model else ()),
        qualified=qualified,
        tests=tests,
    )


# An unqualified equality diagnosis on lower-bound. Until 2026-10-26 this used
# `upper_bound_confusion`, which is now a documented collision (L20 S1 for the original
# problems, case O1) and so gives no equality evidence; `stops_at_first_match` is the other
# equality model on lower-bound and is not.
LB_EQUALITY = attempt(
    "lower-bound",
    Outcome.HYPOTHESIS_SUPPORTED,
    model="stops_at_first_match",
    failing=("duplicates_middle", "duplicates_all"),
)


# ---------------------------------------------------------------------- policy rules
def test_supported_hypothesis_targets_the_models_skill_on_the_densest_problem() -> None:
    # Policy 1.4 on the E2 catalogue (see E2_PROBLEMS).
    rec = POLICY_1_4.recommend(LB_EQUALITY, [LB_EQUALITY], E2_PROBLEMS)
    assert rec.rule is Rule.HYPOTHESIS_SUPPORTED
    assert rec.action is Action.NEW_PROBLEM
    # count-occurrences has 9 tests probing equality_handling, last-less-than 7.
    assert rec.problem_slug == "count-occurrences"
    assert rec.target_skills == ("equality_handling",)
    assert rec.criterion is not None
    assert rec.criterion.skills == ("equality_handling",)
    assert rec.criterion.excluded_model_skills == ("equality_handling",)
    ranking = {r["problem"]: r["probing_tests"] for r in rec.rationale["ranking"]}
    assert ranking == {"count-occurrences": 9, "last-less-than": 7, "lower-bound": 8}


def test_recently_attempted_problems_are_avoided() -> None:
    # Policy 1.4 on the E2 catalogue (see E2_PROBLEMS).
    history = [
        attempt("count-occurrences", Outcome.NO_FAILURE_OBSERVED, n=0),
        attempt(
            "lower-bound",
            Outcome.HYPOTHESIS_SUPPORTED,
            n=1,
            model="upper_bound_confusion",
            failing=("equal_first", "equal_last"),
        ),
    ]
    rec = POLICY_1_4.recommend(history[-1], history, E2_PROBLEMS)
    assert rec.problem_slug == "last-less-than"
    assert rec.rationale["recent_problems"] == ["count-occurrences", "lower-bound"]


def test_single_problem_catalogue_recommends_a_retry_with_a_criterion() -> None:
    only = {"lower-bound": PROBLEMS["lower-bound"]}
    rec = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], only)
    assert rec.action is Action.RETRY
    assert rec.problem_slug == "lower-bound"
    assert rec.criterion is not None


def test_ambiguity_across_skills_prefers_a_problem_modelling_both() -> None:
    # Policy 1.4 on the E2 catalogue (see E2_PROBLEMS).
    index = attempt(
        "lower-bound",
        Outcome.AMBIGUOUS,
        candidates=("hi_init_last_index", "upper_bound_confusion"),
        failing=("equal_first",),
    )
    rec = POLICY_1_4.recommend(index, [index], E2_PROBLEMS)
    assert rec.rule is Rule.AMBIGUOUS
    assert rec.target_skills == ("equality_handling", "search_space_boundaries")
    assert rec.problem_slug == "count-occurrences"  # not recent; both skills modelled
    assert all(r["modelled_skills"] == 2 for r in rec.rationale["ranking"])
    assert rec.criterion is not None
    assert rec.criterion.excluded_model_skills == ()


def test_no_failure_moves_to_a_problem_not_yet_passed_then_stops() -> None:
    # Policy 1.4 on the E2 catalogue (see E2_PROBLEMS).
    first = attempt("lower-bound", Outcome.NO_FAILURE_OBSERVED, n=0)
    rec = POLICY_1_4.recommend(first, [first], E2_PROBLEMS)
    assert (rec.rule, rec.action, rec.problem_slug) == (
        Rule.NO_FAILURE_OBSERVED,
        Action.NEW_PROBLEM,
        "count-occurrences",
    )
    assert rec.criterion is not None
    assert set(rec.criterion.skills) == set(PROBLEMS["count-occurrences"].skills)

    history = [
        first,
        attempt("count-occurrences", Outcome.NO_FAILURE_OBSERVED, n=1),
        attempt("last-less-than", Outcome.NO_FAILURE_OBSERVED, n=2),
    ]
    done = POLICY_1_4.recommend(history[-1], history, E2_PROBLEMS)
    assert (done.action, done.problem_slug, done.criterion) == (Action.NONE, None, None)
    assert "not evidence of complete understanding" in done.rationale["note"]


def test_abstentions_retry_without_a_criterion_and_are_flagged() -> None:
    for outcome in (
        Outcome.UNMODELLED_BEHAVIOUR,
        Outcome.INSUFFICIENT_EVIDENCE,
        Outcome.UNRELIABLE_EVIDENCE,
    ):
        index = attempt("last-less-than", outcome, failing=("empty",))
        rec = POLICY.recommend(index, [index], PROBLEMS)
        assert (rec.rule, rec.action, rec.problem_slug) == (
            Rule.ABSTAINED,
            Action.RETRY,
            "last-less-than",
        )
        assert rec.criterion is None
        assert rec.review_flag


def test_compile_and_execution_errors_retry_without_targeting_a_skill() -> None:
    for outcome in (Outcome.COMPILE_ERROR, Outcome.EXECUTION_ERROR):
        index = attempt("count-occurrences", outcome)
        rec = POLICY.recommend(index, [index], PROBLEMS)
        assert (rec.rule, rec.action, rec.target_skills, rec.criterion) == (
            Rule.NOT_EVALUATED,
            Action.RETRY,
            (),
            None,
        )
        assert not rec.review_flag


def test_policy_is_a_pure_function_of_its_inputs() -> None:
    assert POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS) == POLICY.recommend(
        LB_EQUALITY, [LB_EQUALITY], PROBLEMS
    )


def test_ledger_attributes_tests_to_skills_and_keeps_exclusions_visible() -> None:
    a = attempt("lower-bound", Outcome.UNRELIABLE_EVIDENCE, failing=("empty",), excluded=("empty",))
    ledger = build_ledger([a], PROBLEMS)
    boundaries = [e for e in ledger["search_space_boundaries"] if e.test_key == "empty"]
    assert [e.status for e in boundaries] == [TestStatus.EXCLUDED]
    # Probes empty_input, target_below_all, target_above_all, single_element.
    assert {e.test_key for e in ledger["search_space_boundaries"]} == {
        "empty",
        "below_all",
        "above_all",
        "single_equal",
        "single_above",
        "large_above_all",
    }


# ---------------------------------------------------------------------- follow-up
def test_followup_meeting_the_criterion() -> None:
    rec = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    follow = attempt("count-occurrences", Outcome.NO_FAILURE_OBSERVED, n=5)
    ev = evaluate_followup(
        rec, LB_EQUALITY, PROBLEMS["lower-bound"], follow, PROBLEMS["count-occurrences"]
    )
    assert ev.verdict is Verdict.CRITERION_MET
    assert (ev.passed, ev.failed, ev.excluded) == (9, 0, 0)
    table = {p.probe: (p.index, p.followup) for p in ev.probes}
    assert table == {
        "target_present_duplicates": (ProbeResult.FAILED, ProbeResult.PASSED),
        # LB_EQUALITY (stops_at_first_match since 2026-10-26) fails only duplicate tests.
        "target_present_unique": (ProbeResult.PASSED, ProbeResult.PASSED),
    }
    assert "mastered" not in ev.reason


def test_followup_still_failing_targeted_tests() -> None:
    rec = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    follow = attempt(
        "count-occurrences",
        Outcome.HYPOTHESIS_SUPPORTED,
        n=5,
        model="upper_uses_strict",
        failing=("sample_run", "unique_middle", "run_at_start"),
    )
    ev = evaluate_followup(
        rec, LB_EQUALITY, PROBLEMS["lower-bound"], follow, PROBLEMS["count-occurrences"]
    )
    assert ev.verdict is Verdict.CRITERION_NOT_MET
    assert (ev.passed, ev.failed) == (6, 3)


def test_followup_diagnosed_with_a_model_of_the_targeted_skill_does_not_meet_it() -> None:
    rec = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    # Constructed: the failures fall outside the targeted probes, yet the diagnosis names
    # an equality_handling model. The criterion excludes that explicitly.
    follow = attempt(
        "count-occurrences",
        Outcome.HYPOTHESIS_SUPPORTED,
        n=5,
        model="upper_uses_strict",
        failing=("empty", "below_all"),
    )
    ev = evaluate_followup(
        rec, LB_EQUALITY, PROBLEMS["lower-bound"], follow, PROBLEMS["count-occurrences"]
    )
    assert ev.verdict is Verdict.CRITERION_NOT_MET
    assert ev.failed == 0


def test_followups_without_usable_evidence_are_not_comparable() -> None:
    rec = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    spec = PROBLEMS["count-occurrences"]
    unreliable = attempt("count-occurrences", Outcome.UNRELIABLE_EVIDENCE, n=5)
    assert (
        evaluate_followup(rec, LB_EQUALITY, None, unreliable, spec).verdict
        is Verdict.NOT_COMPARABLE
    )
    equality_tests = tuple(
        t.key for t in spec.tests if "equality_handling" in spec.skills_probed_by(t)
    )
    all_excluded = attempt(
        "count-occurrences", Outcome.NO_FAILURE_OBSERVED, n=5, excluded=equality_tests
    )
    ev = evaluate_followup(rec, LB_EQUALITY, None, all_excluded, spec)
    assert ev.verdict is Verdict.NOT_COMPARABLE
    assert ev.excluded == len(equality_tests)

    retry = POLICY.recommend(
        attempt("count-occurrences", Outcome.UNMODELLED_BEHAVIOUR, failing=("empty",)),
        [],
        PROBLEMS,
    )
    follow = attempt("count-occurrences", Outcome.NO_FAILURE_OBSERVED, n=6)
    assert evaluate_followup(retry, follow, spec, follow, spec).verdict is Verdict.NOT_COMPARABLE


# ------------------------------------------- ledger: explained failures only (ADR-019, C5)
def failures(ledger: Ledger) -> dict[str, list[str]]:
    return {
        skill: [e.test_key for e in entries if e.status is TestStatus.FAILED]
        for skill, entries in ledger.items()
        if any(e.status is TestStatus.FAILED for e in entries)
    }


def test_ledger_attributes_explained_failures_only_to_the_models_skill() -> None:
    looping = (
        "sample_present",
        "sample_absent",
        "above_all",
        "equal_last",
        "duplicates_middle",
        "single_above",
        "two_between",
        "large_absent",
        "large_above_all",
    )
    a = attempt(
        "lower-bound", Outcome.HYPOTHESIS_SUPPORTED, model="no_progress_update", failing=looping
    )
    ledger = build_ledger([a], PROBLEMS)
    # These tests also probe equality, boundaries and specification; before C5 each
    # failure was charged to all of them. Now only the diagnosed model's skill gets it.
    assert failures(ledger) == {"loop_termination": list(looping)}
    assert {
        e.explained_by for e in ledger["loop_termination"] if e.status is TestStatus.FAILED
    } == {"no_progress_update"}


def test_unexplained_failures_are_not_skill_evidence() -> None:
    failing = ("above_all", "single_above", "large_above_all", "equal_first")
    for outcome in (
        Outcome.AMBIGUOUS,
        Outcome.UNMODELLED_BEHAVIOUR,
        Outcome.INSUFFICIENT_EVIDENCE,
        Outcome.UNRELIABLE_EVIDENCE,
    ):
        a = attempt(
            "lower-bound",
            outcome,
            candidates=("hi_init_last_index", "upper_bound_confusion"),
            failing=failing,
        )
        ledger = build_ledger([a], PROBLEMS)
        assert failures(ledger) == {}, outcome
        # Passing tests are still recorded under the skills their probes name.
        passed = {e.test_key for e in ledger["equality_handling"]}
        assert "equal_first" not in passed and "equal_last" in passed


def test_failures_the_selected_model_does_not_own_are_never_reattributed() -> None:
    # A supported diagnosis on a problem whose catalogue entry lacks the model (e.g. a
    # stale record) cannot explain anything.
    a = attempt("lower-bound", Outcome.HYPOTHESIS_SUPPORTED, model="gone", failing=("empty",))
    assert failures(build_ledger([a], PROBLEMS)) == {}


def test_policy_ranking_counts_only_explained_failures() -> None:
    # Policy 1.4 on the E2 catalogue (see E2_PROBLEMS).
    every_test = tuple(t.key for t in PROBLEMS["count-occurrences"].tests)
    history = [
        attempt("count-occurrences", Outcome.UNMODELLED_BEHAVIOUR, n=0, failing=every_test),
        attempt("last-less-than", Outcome.UNMODELLED_BEHAVIOUR, n=1, failing=("empty",)),
        attempt("lower-bound", Outcome.NO_FAILURE_OBSERVED, n=2),
    ]
    rec = POLICY_1_4.recommend(history[-1], history, E2_PROBLEMS)
    assert rec.policy_version == "1.4"
    # Before C5 both problems counted 81 ledger entries: the 15 unexplained failures on
    # count-occurrences and the 1 on last-less-than were charged to every probed skill.
    # (48 and 78 before content change C1 added three probe observations to lower-bound.)
    assert [r["ledger_evidence"] for r in rec.rationale["ranking"]] == [51, 51]


# ------------------------------------------- qualified hypotheses (ADR-019, review item 2)
def test_qualified_or_documented_weak_diagnoses_are_passed_on_as_qualified() -> None:
    weak = attempt(
        "lower-bound",
        Outcome.HYPOTHESIS_SUPPORTED,
        model="hi_init_last_index",
        failing=("above_all", "single_above", "large_above_all"),
        qualified=True,
    )
    rec = POLICY.recommend(weak, [weak], PROBLEMS)
    assert rec.rule is Rule.HYPOTHESIS_SUPPORTED
    assert rec.rationale["qualified_hypothesis"] is True
    assert "clamping" in rec.rationale["known_limitation"]
    # The follow-up still targets the skill, never the specific error.
    assert rec.target_skills == ("search_space_boundaries",)

    strong = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    assert strong.rationale["qualified_hypothesis"] is False
    assert "known_limitation" not in strong.rationale


# ------------------------------------------- follow-up relation (review item 5)
def test_followup_records_its_relation_and_never_claims_mastery() -> None:
    rec = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    follow = attempt("count-occurrences", Outcome.NO_FAILURE_OBSERVED, n=5)
    ev = evaluate_followup(
        rec, LB_EQUALITY, PROBLEMS["lower-bound"], follow, PROBLEMS["count-occurrences"]
    )
    assert ev.relation is Relation.EQUIVALENT_PRACTICE
    assert "equivalent practice problem" in ev.reason
    assert "not evidence of mastery" in ev.reason

    only = {"lower-bound": PROBLEMS["lower-bound"]}
    retry_rec = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], only)
    retry = attempt("lower-bound", Outcome.NO_FAILURE_OBSERVED, n=6)
    ev = evaluate_followup(
        retry_rec, LB_EQUALITY, PROBLEMS["lower-bound"], retry, PROBLEMS["lower-bound"]
    )
    assert ev.verdict is Verdict.CRITERION_MET
    assert ev.relation is Relation.SAME_PROBLEM
    assert "retry of the same problem" in ev.reason


def test_transfer_links_are_reported_as_transfer_but_not_as_demonstrated() -> None:
    lb = PROBLEMS["lower-bound"]
    linked = lb.model_copy(
        update={"curriculum": lb.curriculum.model_copy(update={"transfer": ("last-less-than",)})}
    )
    rec = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    follow = attempt("last-less-than", Outcome.NO_FAILURE_OBSERVED, n=5)
    ev = evaluate_followup(rec, LB_EQUALITY, linked, follow, PROBLEMS["last-less-than"])
    assert ev.relation is Relation.TRANSFER
    assert "not evidence of transfer" in ev.reason


# ---------------------------------------------------------------------- policy 1.3 (E2)
GOLDEN = Path(__file__).parents[1] / "fixtures" / "policy_v1_golden.json"


def test_policy_1_3_reproduces_policy_1_2_on_the_original_problems() -> None:
    # Golden recommendations were produced by policy 1.2 at commit 89a7803, before any
    # non-recommendable problem existed (tests/unit/policy_cases.py says how).
    # 2026-10-25 (L21, owner-approved): the `none` note now says "every recommendable problem";
    # only that string changed in the fixture (6 occurrences), no decision.
    # 2026-10-26 (L20 S1 for the original problems, cases O1-O4; ADR-037): four models gained
    # a known_limitation, so recommendations indexed on them are now passed on as qualified.
    # The fixture is kept as policy 1.2 produced it; `with_s1_original` applies exactly that
    # change (two rationale fields, 12 entries) and nothing else may differ.
    golden = json.loads(GOLDEN.read_text())
    assert len(golden) == 286
    expected, changed = with_s1_original(golden)
    assert changed == 12
    # Since 2026-10-26 more problems are recommendable; the fixture keeps pinning policy 1.4 on
    # the catalogue it was made for.
    assert recommendations(E2_PROBLEMS) == expected
    assert recommendations({s: PROBLEMS[s] for s in ORIGINAL}) == expected


S1_ORIGINAL = {
    "upper_bound_confusion": "lower-bound",
    "uses_le": "last-less-than",
    "clamps_to_zero": "last-less-than",
    "none_sentinel": "first-true",
}


def with_s1_original(golden: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    out = copy.deepcopy(golden)
    changed = 0
    for rec in out:
        rationale = rec["rationale"]
        model = rationale.get("selected_model")
        if model not in S1_ORIGINAL:
            continue
        assert rationale["qualified_hypothesis"] is False and "known_limitation" not in rationale
        spec = PROBLEMS[S1_ORIGINAL[model]]
        rationale["qualified_hypothesis"] = True
        rationale["known_limitation"] = next(
            m.known_limitation for m in spec.error_models if m.key == model
        )
        changed += 1
    return out, changed


def test_non_recommendable_problems_are_never_chosen_but_stay_in_the_catalogue() -> None:
    hidden = {s for s, p in PROBLEMS.items() if not p.recommendable}
    assert hidden, "the demo catalogue has a non-recommendable problem (first-true)"
    for slug in hidden:
        spec = PROBLEMS[slug]
        for outcome, kw in attempts_for(spec):
            rec = POLICY.recommend(record(spec, 0, outcome, kw), [], PROBLEMS)
            # Only the index problem itself can come back, as a retry fallback.
            assert rec.problem_slug is None or rec.problem_slug not in hidden - {slug}
            if rec.problem_slug == slug:
                assert rec.action is Action.RETRY
        for history in histories(PROBLEMS):
            rec = POLICY.recommend(history[-1], history, PROBLEMS)
            assert rec.problem_slug not in hidden
    assert POLICY.version == "1.5"
