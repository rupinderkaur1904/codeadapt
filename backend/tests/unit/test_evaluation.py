"""Evaluation metrics (pure) and the held-out manifests."""

from __future__ import annotations

import pytest

from codeadapt.content import load_catalogue
from codeadapt.diagnosis import Outcome
from codeadapt.evaluation.compare import compare, render_comparison
from codeadapt.evaluation.heldout import CORRECT, UNMODELLED, load_heldout
from codeadapt.evaluation.metrics import CaseResult, Ratio, compute
from codeadapt.evaluation.runner import CaseRow, EvaluationReport, ProblemReport
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


# ------------------------------------------------------------------ method comparison
def report(method_version: str, rows: list[tuple[str, str, str, str | None]]) -> EvaluationReport:
    """rows: (file, truth, outcome, selected model)."""
    results = [
        CaseResult(
            problem="p",
            file=f,
            truth=t,
            outcomes=(Outcome(o), Outcome(o)),
            selected_models=(m, m),
            candidates=(m,) if m else (),
            signatures=(("x",), ("x",)),
        )
        for f, t, o, m in rows
    ]
    metrics = compute(results, {"hi_init_last_index", "stops_at_first_match", "m"})
    return EvaluationReport(
        method="fingerprint_consistency",
        method_version=method_version,
        runs_per_case=2,
        environment={},
        overall=metrics,
        problems=(
            ProblemReport(
                problem="p",
                version="v",
                metrics=metrics,
                identical_model_pairs=(),
                detecting_tests={},
                cases=tuple(
                    CaseRow(
                        file=r.file,
                        truth=r.truth,
                        outcome=r.outcome.value,
                        selected_model=r.selected_model,
                        candidates=r.candidates,
                        classification=r.classification,
                        reproducible=r.reproducible,
                    )
                    for r in results
                ),
            ),
        ),
    )


SUPPORTED = "hypothesis_supported"
INSUFFICIENT = "insufficient_evidence"


def test_comparison_counts_and_lists_changed_cases() -> None:
    a = report(
        "1.1",
        [
            ("e2.cpp", "hi_init_last_index", SUPPORTED, "hi_init_last_index"),
            ("clamp.cpp", UNMODELLED, SUPPORTED, "hi_init_last_index"),
            ("e5.cpp", "stops_at_first_match", SUPPORTED, "stops_at_first_match"),
            ("ok.cpp", CORRECT, "no_failure_observed", None),
        ],
    )
    b = report(
        "2-candidate",
        [
            ("e2.cpp", "hi_init_last_index", INSUFFICIENT, None),
            ("clamp.cpp", UNMODELLED, INSUFFICIENT, None),
            ("e5.cpp", "stops_at_first_match", SUPPORTED, "stops_at_first_match"),
            ("ok.cpp", CORRECT, "no_failure_observed", None),
        ],
    )
    cmp = compare([a, b])
    first, second = cmp.counts
    assert (first.correct_diagnoses, first.false_positive_diagnoses, first.abstentions) == (
        2,
        1,
        0,
    )
    assert (second.correct_diagnoses, second.false_positive_diagnoses, second.abstentions) == (
        1,
        0,
        2,
    )
    assert (first.coverage, second.coverage) == ("3/3", "1/3")
    assert second.abstentions_by_outcome == {INSUFFICIENT: 2}
    assert [c.file for c in cmp.changed] == ["clamp.cpp", "e2.cpp"]
    assert [c.file for c in cmp.focus["hi_init_last_index"]] == ["clamp.cpp", "e2.cpp"]
    assert [c.file for c in cmp.focus["stops_at_first_match"]] == ["e5.cpp"]
    text = render_comparison(cmp)
    assert "| Correct diagnoses | 2 | 1 |" in text
    assert "not an accuracy estimate" in text


def test_comparison_requires_the_same_cases() -> None:
    a = report("1.1", [("x.cpp", "m", SUPPORTED, "m")])
    b = report("2", [("y.cpp", "m", SUPPORTED, "m")])
    with pytest.raises(ValueError, match="same cases"):
        compare([a, b])
