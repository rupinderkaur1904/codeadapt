"""Bank expansion beyond binary search (owner 2026-10-25; ADR-033).

The new families use their own skill keys, so their evidence never touches the four
binary-search skills. Until 2026-10-26 every new problem was non-recommendable, so in these
families a diagnosis retried and a pass stopped (L21). Since the owner's 2026-10-26 decision
(docs/reviews/2026-10-26/recommendability-review.md, option C) all 13 are recommendable, and
the policy moves within the family. These checks run over every non-binary-search problem, so
each later batch is covered automatically.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest

from codeadapt.adaptation import SkillMap, skill_observations
from codeadapt.adaptation.models import Action, Rule
from codeadapt.api.recommendation import recommendation_view
from codeadapt.content.catalogue import Catalogue
from codeadapt.content.models import ProblemSpec
from codeadapt.content.taxonomy import ACTIVE
from codeadapt.db.models import RecommendationRow
from codeadapt.diagnosis import Outcome
from codeadapt.learner.bkt import estimate
from tests.paths import DEMO_CONTENT
from tests.unit.test_adaptation import LB_EQUALITY, POLICY, PROBLEMS, attempt

BINARY_SEARCH_SKILLS = {
    "search_space_boundaries",
    "loop_termination",
    "equality_handling",
    "problem_specification",
}
# ADR-033, revised by ADR-034 (2026-10-26): `index_range` and `update_rule` were split. One
# definition per key, identical in every problem that declares it (the taxonomy enforces it).
NEW_SKILLS = {
    k: ACTIVE[k]
    for k in (
        "accumulator_init",
        "tie_resolution",
        "output_contract",
        "loop_bounds",
        "range_inclusion",
        "window_maintenance",
        "pointer_movement",
        "running_state",
    )
}
NEW = sorted(s for s, p in PROBLEMS.items() if p.family != "binary-search")
BINARY = sorted(s for s, p in PROBLEMS.items() if p.family == "binary-search")


def named_attempt(spec: ProblemSpec, n: int = 1):  # type: ignore[no-untyped-def]
    """An unqualified supported diagnosis with a model that counts as evidence."""
    smap = SkillMap.from_spec(spec, "v")
    for m in spec.error_models:
        failing = tuple(t.key for t in spec.tests if m.key in (t.distinguishes or ()))
        if m.key not in smap.documented_collisions and len(failing) >= 2:
            return m, attempt(
                spec.slug, Outcome.HYPOTHESIS_SUPPORTED, n=n, model=m.key, failing=failing
            )
    raise AssertionError(f"{spec.slug}: no evidence-giving model")


def test_the_bank_has_new_families() -> None:
    assert len(BINARY) == 12
    assert NEW, "no non-binary-search problems"


@pytest.mark.parametrize("slug", NEW)
def test_new_problems_use_only_the_new_skill_keys_with_one_definition(slug: str) -> None:
    spec = PROBLEMS[slug]
    assert set(spec.skills) <= set(NEW_SKILLS), set(spec.skills) - set(NEW_SKILLS)
    assert dict(spec.skills) == {k: NEW_SKILLS[k] for k in spec.skills}


@pytest.mark.parametrize("slug", BINARY)
def test_binary_search_problems_keep_their_four_skills(slug: str) -> None:
    assert set(PROBLEMS[slug].skills) <= BINARY_SEARCH_SKILLS


def family_of(slug: str) -> set[str]:
    return {s for s, p in PROBLEMS.items() if p.family == PROBLEMS[slug].family}


@pytest.mark.parametrize("slug", NEW)
def test_a_supported_diagnosis_stays_in_its_family(slug: str) -> None:
    model, a = named_attempt(PROBLEMS[slug])
    rec = POLICY.recommend(a, [a], PROBLEMS)
    assert rec.rule is Rule.HYPOTHESIS_SUPPORTED
    assert rec.problem_slug in family_of(slug)
    # A retry only when no other problem of the family probes the skill often enough.
    assert rec.action is (Action.RETRY if rec.problem_slug == slug else Action.NEW_PROBLEM)
    assert rec.target_skills == (model.skill,)
    # The evidence lands on the model's new skill only.
    obs = skill_observations([a], PROBLEMS)
    assert {o.skill for o in obs} <= set(NEW_SKILLS)
    assert ("incorrect", model.skill) in {(o.value, o.skill) for o in obs}


@pytest.mark.parametrize("slug", NEW)
def test_a_pass_moves_to_another_problem_of_the_family(slug: str) -> None:
    a = attempt(slug, Outcome.NO_FAILURE_OBSERVED)
    rec = POLICY.recommend(a, [a], PROBLEMS)
    assert rec.rule is Rule.NO_FAILURE_OBSERVED
    assert rec.action is Action.NEW_PROBLEM
    assert rec.problem_slug in family_of(slug) - {slug}


def test_binary_search_recommendations_never_choose_a_new_problem() -> None:
    rec = POLICY.recommend(LB_EQUALITY, [LB_EQUALITY], PROBLEMS)
    assert rec.problem_slug in BINARY
    assert {r["problem"] for r in rec.rationale["ranking"]} <= set(BINARY)


@pytest.mark.parametrize("slug", NEW)
def test_new_evidence_leaves_binary_search_estimates_unchanged(slug: str) -> None:
    _, a = named_attempt(PROBLEMS[slug], n=5)
    before = {s.skill: s for s in estimate([LB_EQUALITY], PROBLEMS).skills}
    after = {s.skill: s for s in estimate([LB_EQUALITY, a], PROBLEMS).skills}
    for skill in BINARY_SEARCH_SKILLS & before.keys():
        assert after[skill].observations == before[skill].observations
    assert set(after) - set(before) <= set(NEW_SKILLS)


# Expansion models whose skill attribution is not unique (L20; ADR-032 route): each is
# output-identical to a program whose cause belongs to a different skill.
NON_UNIQUE = {
    "stock-profit": {"ignores_order"},
    "container-water": {"moves_taller"},
    "dedup-sorted": {"returns_last_index"},
}


def test_non_unique_attributions_are_documented_collisions() -> None:
    for slug in NEW:
        smap = SkillMap.from_spec(PROBLEMS[slug], "v")
        assert set(smap.documented_collisions) == NON_UNIQUE.get(slug, set()), slug


@pytest.mark.parametrize(("slug", "key"), [(s, k) for s, ks in NON_UNIQUE.items() for k in ks])
def test_a_non_unique_diagnosis_adds_no_incorrect_evidence(slug: str, key: str) -> None:
    failing = tuple(t.key for t in PROBLEMS[slug].tests if key in (t.distinguishes or ()))
    assert len(failing) >= 2
    a = attempt(slug, Outcome.HYPOTHESIS_SUPPORTED, model=key, failing=failing)
    assert not [o for o in skill_observations([a], PROBLEMS) if o.value == "incorrect"]
    # Nor does the learner model see an `incorrect` observation for any skill.
    for skill in estimate([a], PROBLEMS).skills:
        assert all(o.observation.value != "incorrect" for o in skill.observations), skill.skill


# L21 wording (owner approval 2026-10-25 13:27): when a pass leaves nothing to recommend, neither
# the stored rationale nor the student message may claim that every problem was passed; only
# recommendable problems are checked. The decision itself is unchanged.
ALL_PASSED_CLAIM = re.compile(r"every problem in (the|this) family", re.IGNORECASE)


@pytest.mark.parametrize(
    "history",
    [
        ["first-max-index", "longest-run", "plus-one", "second-largest", "stock-profit"],
        ["pivot-index", "range-sum-queries"],
        [
            "lower-bound",
            "count-occurrences",
            "last-less-than",
            "first-true",
            "upper-bound",
            "last-occurrence",
            "exact-search",
            "integer-sqrt",  # held: never recommended, so it does not need a pass
        ],
    ],
)
def test_nothing_to_recommend_never_claims_every_problem_was_passed(history: list[str]) -> None:
    attempts = [attempt(s, Outcome.NO_FAILURE_OBSERVED, n=i) for i, s in enumerate(history)]
    rec = POLICY.recommend(attempts[-1], attempts, PROBLEMS)
    assert (rec.action, rec.problem_slug, rec.criterion) == (Action.NONE, None, None)
    assert not ALL_PASSED_CLAIM.search(rec.rationale["note"])
    assert rec.rationale["note"].startswith("Every recommendable problem in the family")
    row = RecommendationRow(
        rule=rec.rule.value,
        action=rec.action.value,
        problem_slug=None,
        target_skills=[],
        rationale=rec.rationale,
        submission_id="s",
        created_at=datetime(2026, 10, 25, tzinfo=UTC),
    )
    view = recommendation_view(Catalogue.load(DEMO_CONTENT), row)
    assert not ALL_PASSED_CLAIM.search(view.message)
    assert view.message == (
        "There is no further problem to recommend here yet. "
        "You can choose any problem from the list."
    )
