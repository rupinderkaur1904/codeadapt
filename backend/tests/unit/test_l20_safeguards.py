"""L20 safeguard S1 (owner approval 2026-10-26): the 11 clear-cut cross-skill twins.

docs/reviews/2026-10-25/l20-search.md found, for each of these models, a program with an
error of a different skill that gives identical output on every committed test and on every
input of the exhaustive and random search domains. No test can tell the two causes apart, so
the attribution to the model's skill is not unique. Each now carries a `known_limitation` (the
ADR-032 process): the diagnosis is kept and shown as qualified, but it adds no `incorrect`
observation and no BKT update. Mappings, fingerprints and the recommendation policy are unchanged.

The two contestable cases (#3 and #13) are not changed (docs/reviews/2026-10-26/
l20-contestable-cases.md); their models still give negative evidence.
"""

from __future__ import annotations

import pytest

from codeadapt.adaptation import SkillMap, skill_observations
from codeadapt.adaptation.models import Rule
from codeadapt.api.feedback import feedback_view
from codeadapt.diagnosis import Outcome
from codeadapt.learner.bkt import estimate
from tests.unit.test_adaptation import POLICY, PROBLEMS, attempt
from tests.unit.test_feedback import CATALOGUE, supported

# (problem, model, skill it maps to). The skill is unchanged; only its evidence is withheld.
S1 = [
    ("upper-bound", "lower_bound_confusion", "equality_handling"),
    ("upper-bound", "hi_init_last_index", "search_space_boundaries"),
    ("upper-bound", "none_sentinel", "problem_specification"),
    ("exact-search", "swapped_direction", "search_space_boundaries"),
    ("exact-search", "lo_init_one", "search_space_boundaries"),
    ("last-occurrence", "returns_first_occurrence", "equality_handling"),
    ("last-occurrence", "stops_at_any_match", "equality_handling"),
    ("last-occurrence", "hi_init_last_index", "search_space_boundaries"),
    ("rotated-search", "left_range_excludes_lo", "equality_handling"),
    ("peak-index", "swapped_direction", "search_space_boundaries"),
    ("integer-sqrt", "strict_square_test", "equality_handling"),
]
CONTESTABLE = [
    ("upper-bound", "returns_last_not_greater", "problem_specification"),
    ("integer-sqrt", "returns_lo_closed", "problem_specification"),
]


def detecting(slug: str, model: str) -> tuple[str, ...]:
    return tuple(t.key for t in PROBLEMS[slug].tests if model in (t.distinguishes or ()))


def named(slug: str, model: str, n: int = 1):  # type: ignore[no-untyped-def]
    return attempt(
        slug, Outcome.HYPOTHESIS_SUPPORTED, n=n, model=model, failing=detecting(slug, model)
    )


def test_exactly_eleven_models_in_six_problems() -> None:
    assert len(S1) == 11 and len({(s, m) for s, m, _ in S1}) == 11
    assert {s for s, _, _ in S1} == {
        "upper-bound",
        "exact-search",
        "last-occurrence",
        "rotated-search",
        "peak-index",
        "integer-sqrt",
    }


@pytest.mark.parametrize(("slug", "model", "skill"), S1)
def test_the_limitation_is_recorded_and_the_mapping_kept(slug: str, model: str, skill: str) -> None:
    spec = next(m for m in PROBLEMS[slug].error_models if m.key == model)
    assert spec.known_limitation is not None
    assert "L20 safeguard S1" in spec.known_limitation
    assert "l20-search.md" in spec.known_limitation
    smap = SkillMap.from_spec(PROBLEMS[slug], "v")
    assert model in smap.documented_collisions
    assert smap.model_skills[model] == skill


@pytest.mark.parametrize(("slug", "model", "skill"), S1)
def test_a_qualified_diagnosis_gives_no_negative_evidence(
    slug: str, model: str, skill: str
) -> None:
    a = named(slug, model)
    assert detecting(slug, model), "the model must fail at least one committed test"
    obs = skill_observations([a], PROBLEMS)
    assert not [o for o in obs if o.value == "incorrect"], (slug, model)
    assert skill not in {o.skill for o in obs}, (slug, model)


@pytest.mark.parametrize(("slug", "model", "skill"), S1)
def test_rule_c_still_credits_the_fully_passed_skills(slug: str, model: str, skill: str) -> None:
    spec = PROBLEMS[slug]
    smap = SkillMap.from_spec(spec, "")
    a = named(slug, model)
    expected = {
        s
        for s in {s for t in spec.tests for s in smap.skills_of(t.key)}
        if all(a.tests[t.key].value == "passed" for t in spec.tests if s in smap.skills_of(t.key))
    }
    got = {o.skill for o in skill_observations([a], PROBLEMS) if o.value == "correct"}
    assert got == expected


@pytest.mark.parametrize(("slug", "model", "skill"), S1)
def test_no_bkt_update_for_the_models_skill(slug: str, model: str, skill: str) -> None:
    assert skill not in {s.skill for s in estimate([named(slug, model)], PROBLEMS).skills}


@pytest.mark.parametrize(("slug", "model", "skill"), S1)
def test_the_diagnosis_is_shown_as_one_possible_cause(slug: str, model: str, skill: str) -> None:
    problem = CATALOGUE.by_slug[slug]
    view = feedback_view(problem, supported(model, list(detecting(slug, model)), "multiple"), [])
    assert view.hint == problem.error_model(model).student_hint
    assert "other mistakes can produce the same pattern" in view.message


@pytest.mark.parametrize(("slug", "model", "skill"), S1)
def test_the_recommendation_is_unchanged_and_marked_qualified(
    slug: str, model: str, skill: str
) -> None:
    a = named(slug, model)
    rec = POLICY.recommend(a, [a], PROBLEMS)
    assert rec.rule is Rule.HYPOTHESIS_SUPPORTED
    assert rec.target_skills == (skill,)
    assert rec.rationale["qualified_hypothesis"] is True
    assert "L20 safeguard S1" in rec.rationale["known_limitation"]


@pytest.mark.parametrize(("slug", "model", "skill"), CONTESTABLE)
def test_the_contestable_cases_are_not_changed(slug: str, model: str, skill: str) -> None:
    spec = next(m for m in PROBLEMS[slug].error_models if m.key == model)
    assert spec.known_limitation is None
    a = named(slug, model)
    incorrect = {(o.skill, o.value) for o in skill_observations([a], PROBLEMS)}
    assert (skill, "incorrect") in incorrect


def test_an_earlier_snapshot_keeps_its_own_attribution() -> None:
    # ADR-023 D4: an attempt stored against a pre-S1 version is attributed with that version's
    # snapshot, which has no collision for these models. Historical evidence is not rewritten.
    old = SkillMap.from_spec(PROBLEMS["upper-bound"], "old").model_copy(
        update={"documented_collisions": ()}
    )
    a = named("upper-bound", "lower_bound_confusion").model_copy(update={"problem_version": "old"})
    obs = skill_observations([a], PROBLEMS, {"old": old})
    assert ("equality_handling", "incorrect") in {(o.skill, o.value) for o in obs}
