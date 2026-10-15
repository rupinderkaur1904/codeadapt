"""Student feedback for supported diagnoses whose evidence is weak (ADR-019)."""

from codeadapt.api.feedback import feedback_view
from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import DiagnosisRow
from codeadapt.diagnosis import Outcome
from tests.paths import DEMO_CONTENT

CATALOGUE = Catalogue.load(DEMO_CONTENT)
LB = CATALOGUE.by_slug["lower-bound"]


def supported(model: str, supporting: list[str], strength: str) -> DiagnosisRow:
    return DiagnosisRow(
        outcome=Outcome.HYPOTHESIS_SUPPORTED.value,
        selected_model=model,
        rationale={"supporting_tests": supporting, "evidence_strength": strength},
    )


def test_strong_diagnosis_names_the_pattern_without_hedging() -> None:
    view = feedback_view(
        LB,
        supported("upper_bound_confusion", ["equal_first", "single_equal"], "multiple"),
        [],
    )
    assert view.hint == LB.error_model("upper_bound_confusion").student_hint
    assert "one possible cause" not in view.message


def test_single_behaviour_or_documented_collision_is_qualified_for_the_student() -> None:
    for model, strength in (
        ("hi_init_last_index", "multiple"),  # documented known_limitation
        ("upper_bound_confusion", "single_behaviour"),  # method qualified it
    ):
        view = feedback_view(LB, supported(model, ["above_all"], strength), [])
        assert "other mistakes can produce the same pattern" in view.message
        assert "one possible cause to check" in view.message
        assert model not in view.message
