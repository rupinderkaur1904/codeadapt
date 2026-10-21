"""Methodology §6.1 metrics over held-out results. Pure; every number is reported as a count.

Ratios are only ever shown next to their numerator and denominator, and a metric whose
denominator is zero is reported as "n/a", never as 0 or 100%.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from codeadapt.diagnosis import Outcome
from codeadapt.evaluation.heldout import CORRECT

LIMITATIONS = (
    "Synthetic held-out cases were written by the same author as the error models, so they "
    "share that author's idea of each bug.",
    "The held-out set is small and is not drawn from real student submissions; its "
    "distribution says nothing about how often each bug occurs in practice.",
    "Selective accuracy here is an upper bound on what real students' code will show.",
    "These results are about the diagnostic method, not about learning; they are not "
    "evidence that CodeAdapt helps anyone learn.",
    "No test checks the O(log n) requirement: a linear scan passes every suite, so nothing "
    "here says anything about complexity.",
)


class Ratio(BaseModel):
    model_config = ConfigDict(frozen=True)

    numerator: int
    denominator: int

    def __str__(self) -> str:
        if self.denominator == 0:
            return f"{self.numerator}/0 (n/a)"
        return f"{self.numerator}/{self.denominator} ({self.numerator / self.denominator:.0%})"


class CaseResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    problem: str
    file: str
    truth: str
    # One entry per repeated evaluation run of the same source.
    outcomes: tuple[Outcome, ...]
    selected_models: tuple[str | None, ...]
    candidates: tuple[str, ...]
    # Per run: the observed signature of every test, in suite order.
    signatures: tuple[tuple[str, ...], ...]

    @property
    def outcome(self) -> Outcome:
        return self.outcomes[0]

    @property
    def selected_model(self) -> str | None:
        return self.selected_models[0]

    @property
    def reproducible(self) -> bool:
        return (
            len(set(self.outcomes)) == 1
            and len(set(self.selected_models)) == 1
            and len(set(self.signatures)) == 1
        )

    @property
    def diagnosed(self) -> bool:
        return self.outcome is Outcome.HYPOTHESIS_SUPPORTED

    @property
    def classification(self) -> str:
        """How this case's result relates to its ground truth."""
        if self.truth == CORRECT:
            return "correct_pass" if self.outcome is Outcome.NO_FAILURE_OBSERVED else "false_alarm"
        if self.diagnosed:
            return "true_diagnosis" if self.selected_model == self.truth else "false_diagnosis"
        # A symptom (ADR-027) names no model, so it is neither a true nor a false diagnosis.
        if self.outcome is Outcome.NON_TERMINATION_OBSERVED:
            return "symptom_reported"
        return "abstained"


class Metrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    cases: int
    buggy_cases: int
    modelled_bug_cases: int
    correct_cases: int
    coverage: Ratio  # buggy cases given HYPOTHESIS_SUPPORTED
    selective_accuracy: Ratio  # diagnosed cases whose model equals the truth
    false_positive_diagnoses: int  # diagnosed with a model other than the truth
    false_negatives: Ratio  # modelled-bug cases that abstained
    correct_code_passed: Ratio  # correct cases with NO_FAILURE_OBSERVED
    abstentions_by_outcome: dict[str, int]  # buggy cases that were not diagnosed
    reproducibility: Ratio  # cases identical across repeated runs


def compute(results: Sequence[CaseResult], model_keys: set[str]) -> Metrics:
    buggy = [r for r in results if r.truth != CORRECT]
    modelled = [r for r in buggy if r.truth in model_keys]
    correct = [r for r in results if r.truth == CORRECT]
    diagnosed = [r for r in results if r.diagnosed]
    return Metrics(
        cases=len(results),
        buggy_cases=len(buggy),
        modelled_bug_cases=len(modelled),
        correct_cases=len(correct),
        coverage=Ratio(numerator=sum(r.diagnosed for r in buggy), denominator=len(buggy)),
        selective_accuracy=Ratio(
            numerator=sum(r.selected_model == r.truth for r in diagnosed),
            denominator=len(diagnosed),
        ),
        false_positive_diagnoses=sum(r.selected_model != r.truth for r in diagnosed),
        false_negatives=Ratio(
            numerator=sum(not r.diagnosed for r in modelled), denominator=len(modelled)
        ),
        correct_code_passed=Ratio(
            numerator=sum(r.outcome is Outcome.NO_FAILURE_OBSERVED for r in correct),
            denominator=len(correct),
        ),
        abstentions_by_outcome=dict(
            sorted(Counter(r.outcome.value for r in buggy if not r.diagnosed).items())
        ),
        reproducibility=Ratio(
            numerator=sum(r.reproducible for r in results), denominator=len(results)
        ),
    )
