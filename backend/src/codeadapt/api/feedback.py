"""Student feedback projection: turns stored evidence into what a student may see.

Rules: hidden tests appear only by number and `student_description`; error-model keys and
descriptions never appear; a hint appears only when a hypothesis is supported.
"""

from __future__ import annotations

from codeadapt.api.schemas import (
    CompileView,
    FeedbackKind,
    FeedbackView,
    TestResultView,
    TestVerdict,
)
from codeadapt.content.loader import LoadedProblem
from codeadapt.content.models import Visibility
from codeadapt.db.models import DiagnosisRow, ExecutionRun, TestObservation
from codeadapt.diagnosis import Outcome
from codeadapt.evidence import OutcomeKind

_KIND_VERDICT = {
    OutcomeKind.RUNTIME_ERROR.value: TestVerdict.RUNTIME_ERROR,
    OutcomeKind.TIME_LIMIT.value: TestVerdict.TIME_LIMIT,
    OutcomeKind.MEMORY_LIMIT.value: TestVerdict.MEMORY_LIMIT,
    OutcomeKind.OUTPUT_LIMIT.value: TestVerdict.OUTPUT_LIMIT,
    OutcomeKind.INFRASTRUCTURE_ERROR.value: TestVerdict.NOT_EVALUATED,
}


def compile_view(run: ExecutionRun) -> CompileView:
    return CompileView(ok=run.compile_status == "ok", diagnostics=run.compile_diagnostics)


def test_views(
    problem: LoadedProblem,
    observations: list[TestObservation],
    reference: dict[str, tuple[str, str]],
) -> list[TestResultView]:
    """`reference` maps test key -> (signature kind, detail) of the reference solution."""
    by_key = {o.test_key: o for o in observations if o.repeat_index == 0}
    views = []
    for number, test in enumerate(problem.spec.tests, start=1):
        obs = by_key.get(test.key)
        if obs is None or obs.excluded_reason is not None:
            verdict = TestVerdict.NOT_EVALUATED
        elif (obs.signature_kind, obs.signature_detail) == reference.get(test.key):
            verdict = TestVerdict.PASSED
        else:
            verdict = _KIND_VERDICT.get(obs.signature_kind, TestVerdict.WRONG_OUTPUT)
        sample = test.visibility is Visibility.SAMPLE
        views.append(
            TestResultView(
                number=number,
                visibility=test.visibility.value,
                description=test.student_description,
                verdict=verdict,
                input=test.input if sample else None,
                expected_output=test.expected if sample else None,
                actual_output=(obs.stdout if obs is not None else None) if sample else None,
            )
        )
    return views


def feedback_view(
    problem: LoadedProblem, diagnosis: DiagnosisRow, tests: list[TestResultView]
) -> FeedbackView:
    outcome = Outcome(diagnosis.outcome)
    failing = [
        t.description
        for t in tests
        if t.verdict not in (TestVerdict.PASSED, TestVerdict.NOT_EVALUATED)
    ]
    match outcome:
        case Outcome.COMPILE_ERROR:
            return FeedbackView(
                kind=FeedbackKind.COMPILE_ERROR,
                message="Your code did not compile. The compiler output above shows where.",
            )
        case Outcome.EXECUTION_ERROR:
            return FeedbackView(
                kind=FeedbackKind.SYSTEM_ERROR,
                message="We could not run your submission because of a problem on our side. "
                "This says nothing about your code; please submit again.",
            )
        case Outcome.UNRELIABLE_EVIDENCE:
            return FeedbackView(
                kind=FeedbackKind.INCONSISTENT_BEHAVIOUR,
                message="Your program did not behave consistently, so we cannot draw conclusions "
                "from these results. Look for reads of uninitialised variables or accesses "
                "outside an array.",
            )
        case Outcome.NO_FAILURE_OBSERVED:
            return FeedbackView(
                kind=FeedbackKind.ALL_TESTS_PASSED,
                message=f"Your solution passed all {len(tests)} tests. Tests can show mistakes but "
                "cannot prove a solution correct for every input.",
            )
        case Outcome.HYPOTHESIS_SUPPORTED:
            model = problem.error_model(diagnosis.selected_model or "")
            supporting = set(diagnosis.rationale.get("supporting_tests", []))
            related = [t.student_description for t in problem.spec.tests if t.key in supporting]
            return FeedbackView(
                kind=FeedbackKind.RECOGNISED_PATTERN,
                message="Your code fails a group of cases in a pattern that a common mistake "
                "produces. Your code behaves as if it has this mistake; check whether it does.",
                hint=model.student_hint,
                related_cases=related,
            )
        case Outcome.AMBIGUOUS | Outcome.UNMODELLED_BEHAVIOUR | Outcome.INSUFFICIENT_EVIDENCE:
            return FeedbackView(
                kind=FeedbackKind.FAILING_CASES,
                message="Your code fails some cases. Compare what these cases have in common.",
                related_cases=failing,
            )
