"""Inputs and outputs of diagnostic methods (pure data; see docs/methodology.md §4)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from codeadapt.evidence.signature import Signature


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Outcome(StrEnum):
    COMPILE_ERROR = "compile_error"
    EXECUTION_ERROR = "execution_error"
    UNRELIABLE_EVIDENCE = "unreliable_evidence"
    NO_FAILURE_OBSERVED = "no_failure_observed"
    UNMODELLED_BEHAVIOUR = "unmodelled_behaviour"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    HYPOTHESIS_SUPPORTED = "hypothesis_supported"
    # v1.2 (ADR-027): a reliable failing test hit the CPU-time limit. A symptom, not a
    # diagnosis: no error model is named and no skill is inferred from it.
    NON_TERMINATION_OBSERVED = "non_termination_observed"

    @property
    def is_diagnosis(self) -> bool:
        return self is Outcome.HYPOTHESIS_SUPPORTED


class Observation(_Frozen):
    """What one test showed about the submission, after reliability marking."""

    test_key: str
    signature: Signature
    # Set when the observation must not be used as evidence (e.g. "non-deterministic",
    # "sanitizer: heap-buffer-overflow"). Excluded observations are listed, never hidden.
    excluded_reason: str | None = None

    @property
    def reliable(self) -> bool:
        return self.excluded_reason is None and self.signature.is_evidence


class DiagnosticInput(_Frozen):
    problem_version: str
    compiled: bool
    observations: tuple[Observation, ...]
    reference: dict[str, Signature]  # test key -> reference behaviour
    models: dict[str, dict[str, Signature]]  # error model key -> test key -> behaviour


class Diagnosis(_Frozen):
    method: str
    method_version: str
    outcome: Outcome
    selected_model: str | None = None
    candidates: tuple[str, ...] = ()
    # Number of reliable tests whose failure the selected model explains.
    support: int = 0
    # Structured, researcher-facing explanation of every step of the decision.
    rationale: dict[str, Any] = Field(default_factory=dict)


class DiagnosticMethod(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def diagnose(self, data: DiagnosticInput) -> Diagnosis: ...
