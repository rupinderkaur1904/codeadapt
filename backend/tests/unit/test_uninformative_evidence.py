"""Rules 8a and 8b (ADR-030): no named error from uninformative evidence.

A model whose fingerprint is constant (8a), or one matched only after tests that separate it
from the reference were excluded (8b), gives `insufficient_evidence`: no selected model, no
hint, no `incorrect` skill observation. v1.2 and v1.1 keep naming it.
"""

from __future__ import annotations

from codeadapt.adaptation import Rule, skill_observations
from codeadapt.api.feedback import feedback_view
from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import DiagnosisRow
from codeadapt.diagnosis import (
    METHODS,
    DiagnosticInput,
    FingerprintConsistencyV1,
    Observation,
    Outcome,
)
from codeadapt.evidence import OutcomeKind, Signature
from tests.paths import DEMO_CONTENT
from tests.unit.test_adaptation import POLICY, PROBLEMS, attempt

METHOD = FingerprintConsistencyV1()
TESTS = ["t1", "t2", "t3", "t4", "t5", "t6"]


def out(v: str) -> Signature:
    return Signature(kind=OutcomeKind.OUTPUT, detail=v)


TLE = Signature(kind=OutcomeKind.TIME_LIMIT)
REFERENCE = {
    "t1": out("3"),
    "t2": out("0"),
    "t3": out("1"),
    "t4": out("2"),
    "t5": out("7"),
    "t6": out("1"),
}


def behaviour(**changes: Signature) -> dict[str, Signature]:
    return {**REFERENCE, **changes}


MODELS = {
    # Prints 0 on every test, like count-occurrences `upper_uses_strict`.
    "always_zero": {t: out("0") for t in TESTS},
    # Differs from the reference on t1, t3, t4.
    "off_by_one": behaviour(t1=out("2"), t3=out("0"), t4=out("1")),
    "stalls": behaviour(t5=TLE, t6=TLE),
}


def observe(sigs: dict[str, Signature], excluded: dict[str, str] | None = None) -> DiagnosticInput:
    excluded = excluded or {}
    return DiagnosticInput(
        problem_version="v",
        compiled=True,
        observations=tuple(
            Observation(test_key=t, signature=s, excluded_reason=excluded.get(t))
            for t, s in sigs.items()
        ),
        reference=REFERENCE,
        models=MODELS,
    )


def test_version_and_selectable_predecessors() -> None:
    assert METHOD.version == "1.3"
    assert METHODS["v1"] == METHOD
    assert METHODS["v1.2"].version == "1.2"
    assert not METHODS["v1.2"].uninformative_is_insufficient
    assert METHODS["v1.2"].time_limit_is_symptom
    assert METHODS["v1.1"].version == "1.1"
    assert not METHODS["v1.1"].uninformative_is_insufficient
    assert not METHODS["v1.1"].time_limit_is_symptom
    assert not METHODS["v2-candidate"].uninformative_is_insufficient


def test_rule8a_constant_fingerprint_is_not_named() -> None:
    d = METHOD.diagnose(observe(MODELS["always_zero"]))
    assert d.outcome is Outcome.INSUFFICIENT_EVIDENCE
    assert d.selected_model is None
    assert d.candidates == ("always_zero",)
    assert d.rationale["rule"] == "8a"
    assert d.rationale["uninformative"] == ["8a"]
    assert d.rationale["consistent_model"] == "always_zero"
    assert d.rationale["informative_tests_excluded"] == []
    assert "ADR-030" in d.rationale["note"]
    # Not a qualified name either: no caveat or evidence strength is recorded.
    assert "evidence_strength" not in d.rationale
    assert "caveat" not in d.rationale


def test_rule8b_excluded_distinguishing_test_is_not_named() -> None:
    sigs = MODELS["off_by_one"]
    d = METHOD.diagnose(observe(sigs, excluded={"t4": "sanitizer: heap-buffer-overflow"}))
    assert d.outcome is Outcome.INSUFFICIENT_EVIDENCE
    assert d.selected_model is None
    assert d.rationale["rule"] == "8b"
    assert d.rationale["informative_tests_excluded"] == ["t4"]
    assert d.support == 2


def test_both_rules_are_recorded_when_both_hold() -> None:
    d = METHOD.diagnose(observe(MODELS["always_zero"], excluded={"t6": "sanitizer: null-pointer"}))
    assert d.outcome is Outcome.INSUFFICIENT_EVIDENCE
    assert d.rationale["uninformative"] == ["8a", "8b"]
    assert d.rationale["rule"] == "8a"


def test_exclusion_of_a_test_the_model_does_not_distinguish_still_names_it() -> None:
    # t2 and t5 are tests on which off_by_one agrees with the reference.
    d = METHOD.diagnose(observe(MODELS["off_by_one"], excluded={"t5": "sanitizer: null-pointer"}))
    assert (d.outcome, d.selected_model) == (Outcome.HYPOTHESIS_SUPPORTED, "off_by_one")
    assert "uninformative" not in d.rationale


def test_informative_model_is_named_as_before() -> None:
    data = observe(MODELS["off_by_one"])
    new, old = METHOD.diagnose(data), METHODS["v1.2"].diagnose(data)
    assert (new.outcome, new.selected_model) == (old.outcome, old.selected_model)
    assert new.outcome is Outcome.HYPOTHESIS_SUPPORTED
    assert new.rationale["rule"] == 8


def test_v1_2_and_v1_1_still_name_uninformative_matches() -> None:
    for data in (
        observe(MODELS["always_zero"]),
        observe(MODELS["off_by_one"], excluded={"t4": "sanitizer: heap-buffer-overflow"}),
    ):
        for name in ("v1.2", "v1.1"):
            d = METHODS[name].diagnose(data)
            assert d.outcome is Outcome.HYPOTHESIS_SUPPORTED, name
            assert "uninformative" not in d.rationale


def test_earlier_rules_take_precedence() -> None:
    # A time limit is a symptom (4b) before any naming rule.
    assert METHOD.diagnose(observe(MODELS["stalls"])).outcome is Outcome.NON_TERMINATION_OBSERVED
    # Too little support stays rule 7, even for a constant model: against this reference the
    # always-zero model differs on t1 only.
    reference = {t: out("0") for t in TESTS} | {"t1": out("3")}
    observed = {t: out("0") for t in TESTS}
    data = observe(observed).model_copy(
        update={"reference": reference, "models": {"always_zero": observed}}
    )
    d = METHOD.diagnose(data)
    assert d.outcome is Outcome.INSUFFICIENT_EVIDENCE
    assert d.rationale["rule"] == 7


# ------------------------------------------------------------------ consumers
def test_consumers_treat_it_as_insufficient_evidence() -> None:
    d = METHOD.diagnose(observe(MODELS["always_zero"]))
    problem = Catalogue.load(DEMO_CONTENT).by_slug["count-occurrences"]
    row = DiagnosisRow(
        outcome=d.outcome.value, selected_model=d.selected_model, rationale=d.rationale
    )
    view = feedback_view(problem, row, [])
    assert view.hint is None
    index = attempt("count-occurrences", Outcome.INSUFFICIENT_EVIDENCE, failing=("sample_run",))
    assert not any(o.value == "incorrect" for o in skill_observations([index], PROBLEMS))
    rec = POLICY.recommend(index, [index], PROBLEMS)
    assert rec.rule is Rule.ABSTAINED
    assert rec.target_skills == ()
