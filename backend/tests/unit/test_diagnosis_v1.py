"""Every decision rule of methodology §4, plus the properties it promises."""

import pytest

from codeadapt.diagnosis import (
    METHODS,
    DiagnosticInput,
    FingerprintConsistencyV1,
    Observation,
    Outcome,
)
from codeadapt.evidence import OutcomeKind, Signature

METHOD = FingerprintConsistencyV1()
TESTS = ["t1", "t2", "t3", "t4", "t5", "t6"]


def out(v: str) -> Signature:
    return Signature(kind=OutcomeKind.OUTPUT, detail=v)


TLE = Signature(kind=OutcomeKind.TIME_LIMIT)
INFRA = Signature(kind=OutcomeKind.INFRASTRUCTURE_ERROR, detail="docker down")
REFERENCE = {t: out("ok") for t in TESTS}


def behaviour(**changes: Signature) -> dict[str, Signature]:
    return {**REFERENCE, **changes}


MODELS = {
    "alpha": behaviour(t1=out("a"), t2=out("a")),  # fails t1, t2
    "beta": behaviour(t3=TLE, t4=TLE, t5=TLE),  # fails t3-t5
    "gamma": behaviour(t6=out("g")),  # detected by one test only
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


def test_rule1_compile_error() -> None:
    data = observe(REFERENCE).model_copy(update={"compiled": False, "observations": ()})
    assert METHOD.diagnose(data).outcome is Outcome.COMPILE_ERROR


@pytest.mark.parametrize("sigs", [{}, behaviour(t2=INFRA)])
def test_rule2_execution_error(sigs: dict[str, Signature]) -> None:
    assert METHOD.diagnose(observe(sigs)).outcome is Outcome.EXECUTION_ERROR


def test_rule3_too_many_exclusions() -> None:
    d = METHOD.diagnose(observe(MODELS["alpha"], {"t3": "nondet", "t4": "nondet", "t5": "ub"}))
    assert d.outcome is Outcome.UNRELIABLE_EVIDENCE
    assert d.rationale["excluded"] == {"t3": "nondet", "t4": "nondet", "t5": "ub"}


def test_rule3_all_failures_excluded() -> None:
    d = METHOD.diagnose(observe(behaviour(t1=out("x")), {"t1": "sanitizer finding"}))
    assert d.outcome is Outcome.UNRELIABLE_EVIDENCE


def test_rule4_no_failure_observed_is_not_correctness() -> None:
    d = METHOD.diagnose(observe(REFERENCE))
    assert d.outcome is Outcome.NO_FAILURE_OBSERVED
    assert "does not prove" in d.rationale["note"]
    assert d.selected_model is None


def test_rule5_unmodelled_behaviour_is_not_forced_into_a_category() -> None:
    # Fails like alpha on t1 but behaves differently on t2: no model is consistent.
    d = METHOD.diagnose(observe(behaviour(t1=out("a"), t2=out("zzz"))))
    assert d.outcome is Outcome.UNMODELLED_BEHAVIOUR
    assert d.selected_model is None
    assert d.rationale["nearest_models"][0]["model"] == "alpha"


def test_rule5_double_bug_abstains() -> None:
    d = METHOD.diagnose(observe(behaviour(t1=out("a"), t2=out("a"), t3=TLE, t4=TLE, t5=TLE)))
    assert d.outcome is Outcome.UNMODELLED_BEHAVIOUR


def test_rule6_indistinguishable_models_are_ambiguous() -> None:
    models = {**MODELS, "alpha_twin": MODELS["alpha"]}
    data = observe(MODELS["alpha"]).model_copy(update={"models": models})
    d = METHOD.diagnose(data)
    assert d.outcome is Outcome.AMBIGUOUS
    assert d.candidates == ("alpha", "alpha_twin")
    assert d.selected_model is None
    assert d.rationale["distinguishing_tests"] == []


def test_rule6_names_excluded_tests_that_would_distinguish() -> None:
    models = {**MODELS, "alpha_prime": behaviour(t1=out("a"), t2=out("a"), t6=out("p"))}
    data = observe(MODELS["alpha"], {"t6": "nondet"}).model_copy(update={"models": models})
    d = METHOD.diagnose(data)
    assert d.outcome is Outcome.AMBIGUOUS
    assert d.rationale["distinguishing_tests"] == ["t6"]


def test_rule7_single_weak_test_is_insufficient() -> None:
    d = METHOD.diagnose(observe(MODELS["gamma"]))
    assert d.outcome is Outcome.INSUFFICIENT_EVIDENCE
    assert d.candidates == ("gamma",)
    assert d.support == 1
    assert d.selected_model is None


@pytest.mark.parametrize(("model", "support"), [("alpha", 2), ("beta", 3)])
def test_rule8_supported_hypothesis(model: str, support: int) -> None:
    d = METHOD.diagnose(observe(MODELS[model]))
    assert d.outcome is Outcome.HYPOTHESIS_SUPPORTED
    assert d.selected_model == model
    assert d.support == support
    assert "not proof" in d.rationale["caveat"]
    assert d.rationale["rule"] == 8


def test_exclusion_below_threshold_still_diagnoses_on_reliable_tests() -> None:
    d = METHOD.diagnose(observe(MODELS["beta"], {"t1": "nondet"}))
    assert d.outcome is Outcome.HYPOTHESIS_SUPPORTED
    assert d.rationale["excluded"] == {"t1": "nondet"}


def test_rationale_records_every_observation() -> None:
    d = METHOD.diagnose(observe(MODELS["beta"]))
    rows = {r["test"]: r for r in d.rationale["tests"]}
    assert set(rows) == set(TESTS)
    assert rows["t3"]["observed"] == "time_limit"
    assert rows["t3"]["agrees_with"] == ["beta"]
    assert d.rationale["contradicting_tests"]["alpha"] == ["t1", "t2", "t3", "t4", "t5"]


def test_parameters_are_recorded_and_adjustable() -> None:
    strict = FingerprintConsistencyV1(min_support=4)
    d = strict.diagnose(observe(MODELS["beta"]))
    assert d.outcome is Outcome.INSUFFICIENT_EVIDENCE
    assert d.rationale["parameters"]["min_support"] == 4


def test_unknown_test_is_a_programming_error() -> None:
    with pytest.raises(ValueError, match="without a reference"):
        METHOD.diagnose(observe({"nope": out("x")}))


# ------------------------------------------- behaviour-group support (ADR-019, change C6)
def test_support_counts_behaviour_groups_and_qualifies_a_single_one() -> None:
    # alpha's two supporting tests are failed by exactly the same models: one behaviour.
    d = METHOD.diagnose(observe(MODELS["alpha"]))
    assert d.outcome is Outcome.HYPOTHESIS_SUPPORTED  # v1 decisions are unchanged
    assert (d.support, d.rationale["support_behaviours"]) == (2, 1)
    assert d.rationale["evidence_strength"] == "single_behaviour"
    assert "cannot be ruled out" in d.rationale["qualification"]


def two_behaviour_input() -> DiagnosticInput:
    # p fails t1-t3; q fails only t2, which splits p's tests into two behaviour groups.
    models = {"p": behaviour(t1=out("p"), t2=out("p"), t3=out("p")), "q": behaviour(t2=out("q"))}
    return observe(models["p"]).model_copy(update={"models": models})


def test_multiple_behaviour_groups_are_not_qualified() -> None:
    d = METHOD.diagnose(two_behaviour_input())
    assert d.outcome is Outcome.HYPOTHESIS_SUPPORTED
    assert d.rationale["support_behaviours"] == 2
    assert d.rationale["evidence_strength"] == "multiple"
    assert "qualification" not in d.rationale


def test_v2_candidate_requires_two_behaviour_groups() -> None:
    candidate = METHODS["v2-candidate"]
    assert candidate.min_behaviours == 2
    weak = candidate.diagnose(observe(MODELS["alpha"]))
    assert weak.outcome is Outcome.INSUFFICIENT_EVIDENCE
    assert weak.candidates == ("alpha",)
    assert weak.rationale["rule"] == 7
    assert weak.rationale["parameters"]["min_behaviours"] == 2
    strong = candidate.diagnose(two_behaviour_input())
    assert (strong.outcome, strong.selected_model) == (Outcome.HYPOTHESIS_SUPPORTED, "p")
    assert METHODS["v1"].min_behaviours == 1


# ------------------------------------------- inconclusive runs (ADR-023, rule R2)
STALL = Signature(kind=OutcomeKind.INCONCLUSIVE)
STALL_REASON = "inconclusive: stopped by the wall clock without reaching the CPU limit, twice"


def test_inconclusive_runs_never_support_a_timeout_model() -> None:
    # beta predicts time limits on t3-t5. Wall-clock stops there are not evidence of it.
    sigs = behaviour(t3=STALL, t4=STALL, t5=STALL)
    d = METHOD.diagnose(observe(sigs, dict.fromkeys(("t3", "t4", "t5"), STALL_REASON)))
    assert d.outcome is Outcome.UNRELIABLE_EVIDENCE
    assert d.selected_model is None


def test_inconclusive_run_is_not_reliable_even_without_a_reason() -> None:
    obs = Observation(test_key="t1", signature=STALL)
    assert not obs.reliable


def test_one_stalled_test_does_not_change_a_supported_diagnosis() -> None:
    sigs = {**MODELS["alpha"], "t6": STALL}
    d = METHOD.diagnose(observe(sigs, {"t6": STALL_REASON}))
    assert d.outcome is Outcome.HYPOTHESIS_SUPPORTED
    assert d.selected_model == "alpha"
