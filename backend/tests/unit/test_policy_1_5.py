"""Policy 1.5: follow-up ranking by evidence instead of test count (ADR-038).

Synthetic attempts over the demo content. These pin the ranking's mechanics; they say nothing
about whether a follow-up helps a learner.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codeadapt.adaptation import PolicyV1
from codeadapt.adaptation.models import Action, Rule
from codeadapt.adaptation.policy_v1 import MIN_PROBING_TESTS
from codeadapt.diagnosis import Outcome
from tests.unit.policy_cases import attempts_for, recommendations, record
from tests.unit.test_adaptation import LB_EQUALITY, PROBLEMS, attempt

P15 = PolicyV1()
P14 = PolicyV1(version="1.4")
BINARY = sorted(s for s, p in PROBLEMS.items() if p.family == "binary-search" and p.recommendable)


def named(slug: str, model: str, n: int = 0):  # type: ignore[no-untyped-def]
    spec = PROBLEMS[slug]
    failing = tuple(t.key for t in spec.tests if model in (t.distinguishes or ()))
    return attempt(slug, Outcome.HYPOTHESIS_SUPPORTED, n=n, model=model, failing=failing)


def test_versions_are_explicit_and_1_4_stays_selectable() -> None:
    assert P15.version == "1.5" and P14.version == "1.4"
    with pytest.raises(ValueError, match="unknown policy version"):
        PolicyV1(version="2.0")


def test_test_count_alone_no_longer_decides() -> None:
    # The known case: with the 2026-10-26 eligibility, 1.4 sends an equality diagnosis on
    # lower-bound to last-occurrence because it has the most equality tests (12), although
    # equality_handling can only gain `correct` observations there (positive-only).
    old = P14.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    new = P15.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    assert old.problem_slug == "last-occurrence"
    assert "equality_handling" in PROBLEMS["last-occurrence"].positive_only_skills
    assert new.problem_slug == "count-occurrences"
    top = new.rationale["ranking"][0]
    assert top["problem"] == "count-occurrences" and top["negative_evidence_possible"] == 1
    # Rule, target skill and criterion are untouched by the ranking change.
    assert (new.rule, new.target_skills, new.criterion) == (
        old.rule,
        old.target_skills,
        old.criterion,
    )


def test_ranking_order_is_recent_then_negative_evidence_then_prior_observations() -> None:
    rec = P15.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    keys = [
        (
            r["recent"],
            -r["negative_evidence_possible"],
            r["prior_observations"],
            -r["probing_share"],
            r["problem"],
        )
        for r in rec.rationale["ranking"]
    ]
    assert keys == sorted(keys)
    assert rec.rationale["ranking"][-1]["problem"] == "lower-bound"  # the index problem is recent


def test_prior_observations_move_the_follow_up_to_a_less_observed_problem() -> None:
    # The learner already has equality observations from count-occurrences (a pass), which is
    # no longer recent after three other attempts. Equal on everything else, the problem that
    # has given fewer observations of the skill comes first. Fewer observations is less
    # evidence from that problem, not a weaker skill.
    history = [
        attempt("count-occurrences", Outcome.NO_FAILURE_OBSERVED, n=0),
        attempt("first-true", Outcome.NO_FAILURE_OBSERVED, n=1),
        attempt("exact-search", Outcome.NO_FAILURE_OBSERVED, n=2),
        named("lower-bound", "stops_at_first_match", n=3),
    ]
    rec = P15.recommend(history[-1], history, PROBLEMS)
    rows = {r["problem"]: r for r in rec.rationale["ranking"]}
    assert rows["count-occurrences"]["prior_observations"] == 1
    assert rows["count-occurrences"]["recent"] is False
    # count-occurrences is the only non-recent problem where equality can get negative evidence,
    # so it still wins; prior observations only order otherwise equal candidates.
    assert rec.problem_slug == "count-occurrences"
    equal = [
        r
        for r in rec.rationale["ranking"]
        if not r["recent"] and r["negative_evidence_possible"] == 0
    ]
    assert [r["prior_observations"] for r in equal] == sorted(
        r["prior_observations"] for r in equal
    )


def test_ties_break_on_share_then_slug_and_are_deterministic() -> None:
    a = named("first-true", "hi_skips_candidate")
    recs = [P15.recommend(a, [a], PROBLEMS) for _ in range(3)]
    assert recs[0] == recs[1] == recs[2]
    rows = recs[0].rationale["ranking"]
    tied = [
        r
        for r in rows
        if (r["recent"], r["negative_evidence_possible"], r["prior_observations"])
        == (rows[0]["recent"], rows[0]["negative_evidence_possible"], rows[0]["prior_observations"])
    ]
    assert [(-r["probing_share"], r["problem"]) for r in tied] == sorted(
        (-r["probing_share"], r["problem"]) for r in tied
    )


def test_a_candidate_needs_the_minimum_number_of_probing_tests() -> None:
    assert MIN_PROBING_TESTS == 2
    for slug in BINARY:
        for outcome, kw in attempts_for(PROBLEMS[slug]):
            rec = P15.recommend(record(PROBLEMS[slug], 0, outcome, kw), [], PROBLEMS)
            for r in rec.rationale.get("ranking", []):
                if "probing_tests" in r and "ledger_evidence" not in r:
                    assert r["probing_tests"] >= MIN_PROBING_TESTS


def test_no_candidate_falls_back_to_a_retry_of_the_same_problem() -> None:
    only = {"lower-bound": PROBLEMS["lower-bound"]}
    rec = P15.recommend(LB_EQUALITY, [LB_EQUALITY], only)
    assert (rec.action, rec.problem_slug) == (Action.RETRY, "lower-bound")
    assert rec.criterion is not None


def test_disabled_problems_never_appear_in_the_ranking() -> None:
    held = {s for s, p in PROBLEMS.items() if not p.recommendable}
    for slug in BINARY:
        for outcome, kw in attempts_for(PROBLEMS[slug]):
            rec = P15.recommend(record(PROBLEMS[slug], 0, outcome, kw), [], PROBLEMS)
            assert not {r["problem"] for r in rec.rationale.get("ranking", [])} & held
            assert rec.problem_slug not in held


def test_ambiguous_diagnoses_still_prefer_problems_modelling_more_candidate_skills() -> None:
    index = attempt(
        "lower-bound",
        Outcome.AMBIGUOUS,
        candidates=("hi_init_last_index", "stops_at_first_match"),
        failing=("equal_first",),
    )
    rec = P15.recommend(index, [index], PROBLEMS)
    assert rec.rule is Rule.AMBIGUOUS
    modelled = [r["modelled_skills"] for r in rec.rationale["ranking"]]
    assert modelled == sorted(modelled, reverse=True)
    assert rec.target_skills == ("equality_handling", "search_space_boundaries")


def test_other_rules_are_identical_to_policy_1_4() -> None:
    # Only supported and ambiguous follow-ups are ranked differently.
    for slug in BINARY:
        for outcome, kw in attempts_for(PROBLEMS[slug]):
            if outcome in (Outcome.HYPOTHESIS_SUPPORTED, Outcome.AMBIGUOUS):
                continue
            a = record(PROBLEMS[slug], 0, outcome, kw)
            old = P14.recommend(a, [a], PROBLEMS).model_dump(exclude={"policy_version"})
            new = P15.recommend(a, [a], PROBLEMS).model_dump(exclude={"policy_version"})
            assert old == new, (slug, outcome)


GOLDEN_1_5 = Path(__file__).parents[1] / "fixtures" / "policy_v1_5_golden.json"


def test_policy_1_5_matches_its_recorded_fixture() -> None:
    # Recorded when 1.5 was introduced (2026-10-26) with
    # `python -m tests.unit.policy_cases 1.5`, on the current eligibility. A change here is a
    # policy change and needs a new version and its own record.
    golden = json.loads(GOLDEN_1_5.read_text())
    assert len(golden) == 286
    assert recommendations(PROBLEMS, "1.5") == golden
