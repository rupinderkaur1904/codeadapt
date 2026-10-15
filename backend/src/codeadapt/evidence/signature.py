"""Outcome signatures: the unit of comparison between a submission and a model.

Two runs "behave the same" on a test exactly when their signatures are equal. The rules
here are deliberately simple and documented in docs/methodology.md §3.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from codeadapt.execution.models import RunResult, RunStatus


class OutcomeKind(StrEnum):
    OUTPUT = "output"
    RUNTIME_ERROR = "runtime_error"
    TIME_LIMIT = "time_limit"
    MEMORY_LIMIT = "memory_limit"
    OUTPUT_LIMIT = "output_limit"
    INFRASTRUCTURE_ERROR = "infrastructure_error"


class Signature(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: OutcomeKind
    # OUTPUT: normalised stdout. RUNTIME_ERROR: "signal:N" or "exit:N". Otherwise empty.
    detail: str = ""

    @property
    def is_evidence(self) -> bool:
        """Infrastructure failures say nothing about the program."""
        return self.kind is not OutcomeKind.INFRASTRUCTURE_ERROR

    def __str__(self) -> str:
        return f"{self.kind.value}:{self.detail}" if self.detail else self.kind.value


def normalise_output(stdout: str) -> str:
    """Strip trailing whitespace on each line and trailing blank lines; keep the rest."""
    lines = [line.rstrip() for line in stdout.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def signature_of(result: RunResult) -> Signature:
    match result.status:
        case RunStatus.OK:
            return Signature(kind=OutcomeKind.OUTPUT, detail=normalise_output(result.stdout))
        case RunStatus.RUNTIME_ERROR:
            detail = (
                f"signal:{result.signal}"
                if result.signal is not None
                else f"exit:{result.exit_code}"
            )
            return Signature(kind=OutcomeKind.RUNTIME_ERROR, detail=detail)
        case RunStatus.TIME_LIMIT:
            return Signature(kind=OutcomeKind.TIME_LIMIT)
        case RunStatus.MEMORY_LIMIT:
            return Signature(kind=OutcomeKind.MEMORY_LIMIT)
        case RunStatus.OUTPUT_LIMIT:
            return Signature(kind=OutcomeKind.OUTPUT_LIMIT)
        case RunStatus.INFRASTRUCTURE_ERROR:
            return Signature(kind=OutcomeKind.INFRASTRUCTURE_ERROR, detail=result.detail)
