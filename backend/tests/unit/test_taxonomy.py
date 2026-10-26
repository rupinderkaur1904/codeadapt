"""L22 skill-taxonomy migration (owner approval 2026-10-26; ADR-034).

`index_range` became `loop_bounds` and `range_inclusion`; `update_rule` became
`window_maintenance`, `pointer_movement` and `running_state`. The retired keys keep their
historical definitions and are rejected in current content. A declared skill that no model
can give negative evidence for needs a written reason.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from codeadapt.api.recommendation import recommendation_view
from codeadapt.content.catalogue import Catalogue
from codeadapt.content.taxonomy import ACTIVE, RETIRED, skill_problems
from codeadapt.db.models import RecommendationRow
from tests.paths import DEMO_CONTENT
from tests.unit.test_adaptation import PROBLEMS

SPEC = PROBLEMS["stock-profit"]


def with_(**changes: Any) -> dict[str, Any]:
    return {**SPEC.model_dump(), **changes}


def validate(data: dict[str, Any]) -> None:
    type(SPEC).model_validate(data)


def test_every_current_problem_uses_only_active_keys_with_their_definitions() -> None:
    for slug, spec in PROBLEMS.items():
        for key, definition in spec.skills.items():
            assert key in ACTIVE, (slug, key)
            assert definition == ACTIVE[key], (slug, key)
        assert {m.skill for m in spec.error_models} <= set(spec.skills), slug
    used = {k for spec in PROBLEMS.values() for k in spec.skills}
    assert not used & set(RETIRED)
    for new in ("loop_bounds", "range_inclusion", "window_maintenance", "pointer_movement"):
        assert new in used
    assert "running_state" in used


def test_retired_keys_keep_their_history_and_name_their_replacements() -> None:
    assert set(RETIRED) == {"index_range", "update_rule"}
    assert RETIRED["index_range"].replaced_by == ("loop_bounds", "range_inclusion")
    assert RETIRED["update_rule"].replaced_by == (
        "window_maintenance",
        "pointer_movement",
        "running_state",
    )
    for r in RETIRED.values():
        assert set(r.replaced_by) <= set(ACTIVE)
        assert r.decision == "ADR-034" and r.retired == "2026-10-26"
    assert not set(RETIRED) & set(ACTIVE)  # a key is never reused


def test_a_retired_key_is_rejected() -> None:
    assert "retired" in skill_problems("index_range", RETIRED["index_range"].definition)[0]
    skills = {**SPEC.skills, "update_rule": RETIRED["update_rule"].definition}
    with pytest.raises(ValidationError, match="'update_rule' was retired"):
        validate(with_(skills=skills))


def test_an_unknown_key_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown skill 'off_by_one'"):
        validate(with_(skills={**SPEC.skills, "off_by_one": "x"}))


def test_a_changed_definition_is_rejected() -> None:
    skills = {**SPEC.skills, "loop_bounds": "Something else."}
    with pytest.raises(ValidationError, match="definition differs"):
        validate(with_(skills=skills))


def test_a_skill_no_model_can_give_negative_evidence_for_needs_a_reason() -> None:
    # container-water's only `pointer_movement` model carries a known_limitation (ADR-032).
    cw = PROBLEMS["container-water"]
    assert set(cw.positive_only_skills) == {"pointer_movement"}
    with pytest.raises(ValidationError, match="'pointer_movement': no error model"):
        type(cw).model_validate({**cw.model_dump(), "positive_only_skills": {}})
    with pytest.raises(ValidationError, match="'pointer_movement': no error model"):
        type(cw).model_validate(
            {**cw.model_dump(), "positive_only_skills": {"pointer_movement": " "}}
        )
    # A model whose every mapping carries a known_limitation counts as none.
    models = [
        {**m.model_dump(), "known_limitation": "x"} if m.skill == "loop_bounds" else m.model_dump()
        for m in SPEC.error_models
    ]
    with pytest.raises(ValidationError, match="'loop_bounds': no error model"):
        validate(with_(error_models=models))


def test_a_stale_or_undeclared_exemption_is_rejected() -> None:
    reasons = {**SPEC.positive_only_skills, "loop_bounds": "no"}
    with pytest.raises(ValidationError, match="'loop_bounds' has a model"):
        validate(with_(positive_only_skills=reasons))
    reasons = {**SPEC.positive_only_skills, "running_state": "no"}
    with pytest.raises(ValidationError, match="undeclared skill 'running_state'"):
        validate(with_(positive_only_skills=reasons))


def test_pivot_index_has_models_for_its_mapped_skill() -> None:
    spec = PROBLEMS["pivot-index"]
    assert set(spec.skills) == {"tie_resolution", "output_contract", "range_inclusion"}
    models = {m.key: m.skill for m in spec.error_models}
    assert models["pivot_counted_left"] == models["pivot_counted_right"] == "range_inclusion"
    assert not any(m.known_limitation for m in spec.error_models if m.skill == "range_inclusion")
    assert "range_inclusion" not in spec.positive_only_skills


def test_every_positive_only_skill_is_written_down() -> None:
    for slug, spec in PROBLEMS.items():
        for skill in spec.skills:
            capable = [m for m in spec.error_models if m.skill == skill and not m.known_limitation]
            assert bool(capable) != (skill in spec.positive_only_skills), (slug, skill)


def test_a_stored_recommendation_on_a_retired_key_keeps_its_historical_focus() -> None:
    def row(skills: list[str]) -> RecommendationRow:
        return RecommendationRow(
            rule="hypothesis_supported",
            action="retry",
            problem_slug="stock-profit",
            target_skills=skills,
            rationale={},
            submission_id="s",
            created_at=datetime(2026, 10, 25, tzinfo=UTC),
        )

    catalogue = Catalogue.load(DEMO_CONTENT)
    old = recommendation_view(catalogue, row(["index_range"]))
    assert old.focus == [RETIRED["index_range"].definition]
    new = recommendation_view(catalogue, row(["loop_bounds"]))
    assert new.focus == [ACTIVE["loop_bounds"]]
    assert recommendation_view(catalogue, row(["no_such_key"])).focus == []
