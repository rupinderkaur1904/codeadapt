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
# v1.1 is kept to reproduce every result recorded before ADR-027; tests of a time-limit model
# being named (beta) run against it.
V11 = METHODS["v1.1"]
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
    double = observe(behaviour(t1=out("a"), t2=out("a"), t3=out("b")))
    assert METHOD.diagnose(double).outcome is Outcome.UNMODELLED_BEHAVIOUR
    # alpha's bug plus beta's time limits: v1.1 abstained as unmodelled; v1.2 reports the
    # time limit as a symptom (rule 4b runs before rule 5).
    with_stall = observe(behaviour(t1=out("a"), t2=out("a"), t3=TLE, t4=TLE, t5=TLE))
    assert V11.diagnose(with_stall).outcome is Outcome.UNMODELLED_BEHAVIOUR
    assert METHOD.diagnose(with_stall).outcome is Outcome.NON_TERMINATION_OBSERVED


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


@pytest.mark.parametrize(
    ("method", "model", "support"), [(METHOD, "alpha", 2), (V11, "alpha", 2), (V11, "beta", 3)]
)
def test_rule8_supported_hypothesis(
    method: FingerprintConsistencyV1, model: str, support: int
) -> None:
    d = method.diagnose(observe(MODELS[model]))
    assert d.outcome is Outcome.HYPOTHESIS_SUPPORTED
    assert d.selected_model == model
    assert d.support == support
    assert "not proof" in d.rationale["caveat"]
    assert d.rationale["rule"] == 8


def test_exclusion_below_threshold_still_diagnoses_on_reliable_tests() -> None:
    d = V11.diagnose(observe(MODELS["beta"], {"t1": "nondet"}))
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
    strict = FingerprintConsistencyV1(min_support=4, time_limit_is_symptom=False)
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


# ------------------------------------------- time limits are a symptom (ADR-027, rule 4b)
def test_rule4b_time_limit_is_reported_as_a_symptom_not_a_model() -> None:
    d = METHOD.diagnose(observe(MODELS["beta"]))
    assert d.outcome is Outcome.NON_TERMINATION_OBSERVED
    assert not d.outcome.is_diagnosis
    assert d.selected_model is None
    assert d.candidates == ()
    assert d.rationale["rule"] == "4b"
    assert d.rationale["timed_out_tests"] == ["t3", "t4", "t5"]
    assert d.rationale["other_failing_tests"] == []
    # The models it is consistent with are kept for research, under their own key only.
    assert d.rationale["consistent_models"] == ["beta"]
    assert "candidates" not in d.rationale
    assert "no error model is named" in d.rationale["note"]


def test_rule4b_v1_1_still_names_the_time_limit_model() -> None:
    d = V11.diagnose(observe(MODELS["beta"]))
    assert (d.method_version, d.outcome, d.selected_model) == (
        "1.1",
        Outcome.HYPOTHESIS_SUPPORTED,
        "beta",
    )
    assert METHOD.version == "1.2"
    assert METHODS["v1"] == METHOD


def test_rule4b_applies_with_other_failures_and_without_candidates() -> None:
    # A time limit plus a wrong output that no model predicts: still a symptom, not
    # unmodelled, and the other failing test is listed.
    d = METHOD.diagnose(observe(behaviour(t3=TLE, t1=out("zzz"))))
    assert d.outcome is Outcome.NON_TERMINATION_OBSERVED
    assert d.rationale["timed_out_tests"] == ["t3"]
    assert d.rationale["other_failing_tests"] == ["t1"]
    assert d.rationale["consistent_models"] == []


def test_rule4b_a_time_limit_on_every_test_is_a_symptom() -> None:
    d = METHOD.diagnose(observe(dict.fromkeys(TESTS, TLE)))
    assert d.outcome is Outcome.NON_TERMINATION_OBSERVED
    assert d.rationale["timed_out_tests"] == TESTS


def test_rule4b_ignores_time_limits_on_excluded_tests() -> None:
    # A sanitizer stack-overflow on the test that timed out excludes it (VAL1-A C_AOR_018):
    # the remaining reliable failure decides, as in v1.1.
    sigs = {**MODELS["alpha"], "t3": TLE}
    d = METHOD.diagnose(observe(sigs, {"t3": "sanitizer: stack-overflow"}))
    assert (d.outcome, d.selected_model) == (Outcome.HYPOTHESIS_SUPPORTED, "alpha")


@pytest.mark.parametrize(
    ("sigs", "excluded", "outcome"),
    [
        # Infrastructure error anywhere wins (rule 2).
        (behaviour(t3=TLE, t1=INFRA), {}, Outcome.EXECUTION_ERROR),
        # Too many exclusions wins (rule 3), even with a reliable time limit.
        (
            behaviour(t3=TLE, t4=out("x"), t5=out("x"), t6=out("x")),
            {"t4": "ub", "t5": "ub", "t6": "nondet"},
            Outcome.UNRELIABLE_EVIDENCE,
        ),
        # A time limit only on an excluded test, with no other failure: unreliable.
        (behaviour(t3=TLE), {"t3": "sanitizer: stack-overflow"}, Outcome.UNRELIABLE_EVIDENCE),
        # Wall-clock stops are inconclusive, never a time limit (ADR-023).
        (
            behaviour(t3=STALL, t4=STALL, t5=STALL),
            dict.fromkeys(("t3", "t4", "t5"), STALL_REASON),
            Outcome.UNRELIABLE_EVIDENCE,
        ),
        # A crash is a runtime error, not a time limit: ordinary evidence, unmodelled here.
        (
            behaviour(t3=Signature(kind=OutcomeKind.RUNTIME_ERROR, detail="signal:11")),
            {},
            Outcome.UNMODELLED_BEHAVIOUR,
        ),
    ],
)
def test_rule4b_precedence(
    sigs: dict[str, Signature], excluded: dict[str, str], outcome: Outcome
) -> None:
    assert METHOD.diagnose(observe(sigs, excluded)).outcome is outcome


def test_rule4b_parameter_is_recorded() -> None:
    d = METHOD.diagnose(observe(MODELS["alpha"]))
    assert d.rationale["parameters"]["time_limit_is_symptom"] is True
