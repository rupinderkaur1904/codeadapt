"""Which problems the recommendation policy may choose (owner decision 2026-10-26, option C).

docs/reviews/2026-10-26/recommendability-review.md reviewed the 22 problems that CE1 decision
E2 kept out. The owner enabled the reviewed subset and held five binary-search problems. These
checks pin the exact sets and that every enabled problem has what the policy needs.
"""

from __future__ import annotations

import pytest

from codeadapt.adaptation.ledger import tests_probing as probing_tests
from codeadapt.adaptation.models import Action
from tests.unit.policy_cases import attempts_for, record
from tests.unit.test_adaptation import POLICY, PROBLEMS

ORIGINAL = {"lower-bound", "count-occurrences", "last-less-than"}
ENABLED_2026_10_26 = {
    # binary search
    "first-true",
    "upper-bound",
    "last-occurrence",
    "exact-search",
    # arrays
    "first-max-index",
    "longest-run",
    "plus-one",
    "second-largest",
    "stock-profit",
    # two-pointers
    "closest-pair-sum",
    "container-water",
    "dedup-sorted",
    # sliding-window
    "distinct-in-windows",
    "longest-sum-at-most",
    "max-window-sum",
    # prefix-sums
    "pivot-index",
    "range-sum-queries",
}
# Held by the review: see its section 3 for each reason.
HELD = {"integer-sqrt", "min-capacity", "peak-index", "rotated-search", "rotated-min"}


def test_the_recommendable_set_is_exactly_the_reviewed_one() -> None:
    assert len(PROBLEMS) == 25
    assert set(PROBLEMS) == ORIGINAL | ENABLED_2026_10_26 | HELD
    assert {s for s, p in PROBLEMS.items() if p.recommendable} == ORIGINAL | ENABLED_2026_10_26
    assert {s for s, p in PROBLEMS.items() if not p.recommendable} == HELD


@pytest.mark.parametrize("slug", sorted(ORIGINAL | ENABLED_2026_10_26))
def test_every_recommendable_problem_can_serve_as_a_follow_up(slug: str) -> None:
    spec = PROBLEMS[slug]
    assert spec.title.strip()
    # Every declared skill is probed by a test, so a follow-up criterion on it can be judged.
    for skill in spec.skills:
        assert probing_tests(spec, {skill}), f"{slug}: no test probes {skill}"
    # Every error model names a declared skill (also checked when the content loads).
    assert {m.skill for m in spec.error_models} <= set(spec.skills)
    # A family-mate exists, so a follow-up can be a different problem.
    assert [p for p in PROBLEMS.values() if p.family == spec.family and p.slug != slug]


@pytest.mark.parametrize("slug", sorted(PROBLEMS))
def test_held_problems_are_never_chosen_after_any_attempt(slug: str) -> None:
    spec = PROBLEMS[slug]
    for outcome, kw in attempts_for(spec):
        rec = POLICY.recommend(record(spec, 0, outcome, kw), [], PROBLEMS)
        if rec.problem_slug in HELD:
            # The one route a held problem has: a retry of itself, never a new problem.
            assert rec.problem_slug == slug and rec.action is Action.RETRY, (slug, outcome)
