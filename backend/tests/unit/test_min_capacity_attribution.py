"""Owner decision 2026-10-25, option (b) for L20: min-capacity's exact-boundary diagnoses.

`strict_day_limit` and `full_day_overflows` are output-identical, on every valid input, to
programs with a counting or specification error (docs/reviews/2026-10-25/
skill-mapping-review.md). Their attribution to `equality_handling` is therefore not unique.
Both now carry a documented `known_limitation`, the existing documented-collision route
(ADR-019, ADR-023 D2): the diagnosis is kept and shown as qualified, but it adds no
`incorrect` observation and no BKT update for `equality_handling`. Nothing else changes.
"""

from __future__ import annotations

from codeadapt.adaptation import SkillMap, TestStatus, build_ledger, skill_observations
from codeadapt.adaptation.models import Rule
from codeadapt.api.feedback import feedback_view
from codeadapt.diagnosis import Outcome
from codeadapt.learner.bkt import estimate
from tests.unit.test_adaptation import LB_EQUALITY, POLICY, PROBLEMS, attempt
from tests.unit.test_feedback import CATALOGUE, supported

MC = PROBLEMS["min-capacity"]
MC_LOADED = CATALOGUE.by_slug["min-capacity"]
AMBIGUOUS_ATTRIBUTION = ("full_day_overflows", "strict_day_limit")
# Documented collisions of every other problem, unchanged by this decision.
# Updated 2026-10-26 for L20 safeguard S1 (owner-approved): the 11 clear-cut cross-skill twins
# in the six searched problems now carry a known_limitation too (tests/unit/test_l20_safeguards.py).
OTHER_COLLISIONS = {
    "count-occurrences": ("hi_init_last_index",),
    "exact-search": ("lo_init_one", "swapped_direction"),
    "first-true": ("hi_init_last_index",),
    "integer-sqrt": ("strict_square_test",),
    "last-less-than": ("hi_init_last_index",),
    "last-occurrence": (
        "hi_init_last_index",
        "missing_equality_check",
        "returns_first_occurrence",
        "stops_at_any_match",
    ),
    "lower-bound": ("hi_init_last_index",),
    "peak-index": ("swapped_direction",),
    "rotated-min": ("hi_skips_candidate",),
    "rotated-search": ("left_half_test_strict", "left_range_excludes_lo"),
    "upper-bound": ("hi_init_last_index", "lower_bound_confusion", "none_sentinel"),
}


def detecting(model: str) -> tuple[str, ...]:
    """The tests on which `model` differs from the reference (the measured `distinguishes`)."""
    return tuple(t.key for t in MC.tests if model in (t.distinguishes or ()))


def named(model: str, n: int = 1):  # type: ignore[no-untyped-def]
    # Unqualified by the method: both models span several behaviour groups (5 and 6).
    return attempt(
        "min-capacity", Outcome.HYPOTHESIS_SUPPORTED, n=n, model=model, failing=detecting(model)
    )


def test_both_models_are_documented_collisions_and_keep_their_skill() -> None:
    smap = SkillMap.from_spec(MC, "v")
    assert set(AMBIGUOUS_ATTRIBUTION) <= set(smap.documented_collisions)
    # The mapping itself is unchanged: the skill is still recorded, only not as evidence.
    assert {m: smap.model_skills[m] for m in AMBIGUOUS_ATTRIBUTION} == {
        "full_day_overflows": "equality_handling",
        "strict_day_limit": "equality_handling",
    }
    assert smap.documented_collisions == AMBIGUOUS_ATTRIBUTION


def test_no_other_problem_or_model_changed() -> None:
    for slug, expected in OTHER_COLLISIONS.items():
        assert SkillMap.from_spec(PROBLEMS[slug], "v").documented_collisions == expected, slug
    # The other min-capacity models still count as evidence for their skill.
    assert not {"lo_init_one", "hi_skips_candidate", "no_progress_update", "sorts_weights"} & set(
        SkillMap.from_spec(MC, "v").documented_collisions
    )


def test_ambiguous_diagnosis_adds_no_negative_equality_observation() -> None:
    for model in AMBIGUOUS_ATTRIBUTION:
        a = named(model)
        assert len(detecting(model)) >= 2
        obs = skill_observations([a], PROBLEMS)
        assert not [o for o in obs if o.value == "incorrect"], model
        assert "equality_handling" not in {o.skill for o in obs}, model
        # The failures are not charged to any skill in the ledger either.
        ledger = build_ledger([a], PROBLEMS)
        assert not [
            e for items in ledger.values() for e in items if e.status is TestStatus.FAILED
        ], model


def test_rule_c_is_unchanged_for_the_other_skills() -> None:
    # Rule C (L19, not changed): a skill whose every probing test passed still gets `correct`.
    for model in AMBIGUOUS_ATTRIBUTION:
        a = named(model)
        smap = SkillMap.from_spec(MC, "")
        expected = {
            skill
            for skill in {s for t in MC.tests for s in smap.skills_of(t.key)}
            if all(
                a.tests[t.key] is TestStatus.PASSED
                for t in MC.tests
                if skill in smap.skills_of(t.key)
            )
        }
        got = {o.skill for o in skill_observations([a], PROBLEMS) if o.value == "correct"}
        assert got == expected, model


def test_no_bkt_update_for_equality_handling() -> None:
    # A learner with one counted equality observation from lower-bound (incorrect).
    before = estimate([LB_EQUALITY], PROBLEMS)
    for model in AMBIGUOUS_ATTRIBUTION:
        after = estimate([LB_EQUALITY, named(model, n=7)], PROBLEMS)
        eq_before = next(s for s in before.skills if s.skill == "equality_handling")
        eq_after = next(s for s in after.skills if s.skill == "equality_handling")
        assert eq_after.counted == eq_before.counted == 1
        assert eq_after.observations == eq_before.observations
        assert eq_after.observations[-1].p_known_after == eq_before.observations[-1].p_known_after
        assert all(o.observation.problem_slug == "lower-bound" for o in eq_after.observations)
    # On its own, the min-capacity attempt gives equality_handling no estimate at all.
    alone = estimate([named("strict_day_limit")], PROBLEMS)
    assert "equality_handling" not in {s.skill for s in alone.skills}


def test_an_unaffected_min_capacity_model_still_gives_negative_evidence() -> None:
    a = named("sorts_weights")
    incorrect = [o for o in skill_observations([a], PROBLEMS) if o.value == "incorrect"]
    assert [(o.skill, o.basis) for o in incorrect] == [
        ("problem_specification", "supported diagnosis: sorts_weights")
    ]


def test_diagnosis_is_kept_and_shown_as_one_possible_cause() -> None:
    for model in AMBIGUOUS_ATTRIBUTION:
        view = feedback_view(MC_LOADED, supported(model, list(detecting(model)), "multiple"), [])
        # The hint stays; the wording says other mistakes produce the same pattern.
        assert view.hint == MC_LOADED.error_model(model).student_hint
        assert "other mistakes can produce the same pattern" in view.message
        assert model not in view.message


def test_recommendation_choice_is_unchanged_and_marked_qualified() -> None:
    # Policy 1.4 is not changed: same rule and target skill; the rationale says "qualified".
    for model in AMBIGUOUS_ATTRIBUTION:
        a = named(model)
        rec = POLICY.recommend(a, [a], PROBLEMS)
        assert rec.rule is Rule.HYPOTHESIS_SUPPORTED
        assert rec.target_skills == ("equality_handling",)
        assert rec.rationale["selected_model"] == model
        assert rec.rationale["qualified_hypothesis"] is True
        assert "L20" in rec.rationale["known_limitation"]


def test_a_snapshot_of_the_earlier_content_version_keeps_its_own_attribution() -> None:
    # ADR-023 D4: attempts are attributed with their own version's snapshot. A snapshot taken
    # before this decision has no documented collision for these models, so attempts stored
    # against that version keep their original evidence. No such attempt exists outside
    # development and test databases; this pins the documented behaviour.
    old = SkillMap.from_spec(MC, "old").model_copy(update={"documented_collisions": ()})
    a = named("strict_day_limit").model_copy(update={"problem_version": "old"})
    obs = skill_observations([a], PROBLEMS, {"old": old})
    assert ("equality_handling", "incorrect") in {(o.skill, o.value) for o in obs}
