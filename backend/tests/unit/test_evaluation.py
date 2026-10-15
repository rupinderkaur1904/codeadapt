"""Evaluation metrics (pure) and the held-out manifests."""

from __future__ import annotations

from codeadapt.content import load_catalogue
from codeadapt.diagnosis import Outcome
from codeadapt.evaluation.heldout import CORRECT, UNMODELLED, load_heldout
from codeadapt.evaluation.metrics import CaseResult, Ratio, compute
from tests.paths import DEMO_CONTENT, HELDOUT


def case(
    truth: str,
    outcome: Outcome,
    model: str | None = None,
    *,
    second: Outcome | None = None,
) -> CaseResult:
    outcomes = (outcome, second or outcome)
    return CaseResult(
        problem="p",
        file=f"{truth}-{outcome.value}.cpp",
        truth=truth,
        outcomes=outcomes,
        selected_models=(model, model),
        candidates=(model,) if model else (),
        signatures=(("output:1",), ("output:1",)),
    )


def test_metrics_are_counts_with_explicit_denominators() -> None:
    results = [
        case("m1", Outcome.HYPOTHESIS_SUPPORTED, "m1"),  # true diagnosis
        case("m2", Outcome.HYPOTHESIS_SUPPORTED, "m1"),  # false diagnosis
        case("m2", Outcome.AMBIGUOUS),  # abstained (false negative)
        case(UNMODELLED, Outcome.UNMODELLED_BEHAVIOUR),  # correct abstention
        case(CORRECT, Outcome.NO_FAILURE_OBSERVED),
        case(CORRECT, Outcome.INSUFFICIENT_EVIDENCE, second=Outcome.AMBIGUOUS),  # false alarm
    ]
    m = compute(results, {"m1", "m2"})
    assert (m.cases, m.buggy_cases, m.modelled_bug_cases, m.correct_cases) == (6, 4, 3, 2)
    assert m.coverage == Ratio(numerator=2, denominator=4)
    assert m.selective_accuracy == Ratio(numerator=1, denominator=2)
    assert m.false_positive_diagnoses == 1
    assert m.false_negatives == Ratio(numerator=1, denominator=3)
    assert m.correct_code_passed == Ratio(numerator=1, denominator=2)
    assert m.abstentions_by_outcome == {"ambiguous": 1, "unmodelled_behaviour": 1}
    assert m.reproducibility == Ratio(numerator=5, denominator=6)
    assert [r.classification for r in results] == [
        "true_diagnosis",
        "false_diagnosis",
        "abstained",
        "abstained",
        "correct_pass",
        "false_alarm",
    ]


def test_empty_denominators_are_not_reported_as_percentages() -> None:
    m = compute([case(CORRECT, Outcome.NO_FAILURE_OBSERVED)], set())
    assert str(m.selective_accuracy) == "0/0 (n/a)"
    assert str(m.coverage) == "0/0 (n/a)"
    assert str(m.correct_code_passed) == "1/1 (100%)"


def test_heldout_manifests_reference_real_problems_and_models() -> None:
    problems = {p.spec.slug: p.spec for p in load_catalogue(DEMO_CONTENT)}
    cases = load_heldout(HELDOUT)
    assert {c.problem for c in cases} == set(problems)
    for c in cases:
        models = {m.key for m in problems[c.problem].error_models}
        assert c.truth in models | {CORRECT, UNMODELLED}, c
        assert c.source.strip()
    # Every problem has at least one correct case and one case outside the model space.
    for slug in problems:
        truths = {c.truth for c in cases if c.problem == slug}
        assert {CORRECT, UNMODELLED} <= truths
    assert load_heldout(HELDOUT, {"lower-bound"}) == [
        c for c in cases if c.problem == "lower-bound"
    ]
