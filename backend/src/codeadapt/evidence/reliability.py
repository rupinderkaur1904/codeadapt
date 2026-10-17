"""Reliability marking: decide which observations may be used as evidence.

Pure functions over run results (docs/methodology.md §3). An observation is excluded when
a sanitizer build reports undefined behaviour on that test, when a repeated run of the
same binary on the same input produced a different outcome signature, or when the run was
inconclusive (stopped by the wall clock without reaching its CPU limit, ADR-023).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from pydantic import BaseModel, ConfigDict

from codeadapt.evidence.signature import OutcomeKind, Signature, signature_of
from codeadapt.execution.models import RunResult

_ASAN = re.compile(r"ERROR: AddressSanitizer: ([a-z-]+)")
_UBSAN = re.compile(r"runtime error: ([^\n]+)")
_LEAK = "ERROR: LeakSanitizer"


class SanitizerFinding(BaseModel):
    model_config = ConfigDict(frozen=True)

    tool: str  # "asan" | "ubsan"
    kind: str  # e.g. "heap-buffer-overflow", "signed-integer-overflow"
    message: str  # first line of the report, for researchers (never shown to students)


# Student-facing phrasing per finding kind. Unknown kinds fall back to a generic sentence.
STUDENT_PHRASES: dict[str, str] = {
    "heap-buffer-overflow": "reads or writes outside the bounds of an array or vector",
    "stack-buffer-overflow": "reads or writes outside the bounds of a local array",
    "global-buffer-overflow": "reads or writes outside the bounds of a global array",
    "container-overflow": "reads or writes past the end of a container's elements",
    "heap-use-after-free": "uses memory after it has been freed",
    "stack-use-after-scope": "uses a local variable after it has gone out of scope",
    "stack-overflow": "recurses too deeply (stack overflow)",
    "double-free": "frees the same memory twice",
    "signed-integer-overflow": "overflows a signed integer",
    "index-out-of-bounds": "indexes an array out of bounds",
    "division-by-zero": "divides by zero",
    "shift": "performs an invalid bit shift",
    "null-pointer": "dereferences a null pointer",
    "invalid-value": "reads a value that is not valid for its type (often uninitialised)",
}
GENERIC_PHRASE = "performs an operation with undefined behaviour"

# Version of the execution-evidence rules (docs/component-interfaces.md §3), recorded with
# every diagnosis. 1: CPU-limit timeouts are evidence; wall-only stops are re-run once and
# are otherwise inconclusive.
# 2: a run whose streams lack the end-of-output marker is an infrastructure error (ADR-024).
EVIDENCE_RULES_VERSION = "2"
INCONCLUSIVE_REASON = (
    "inconclusive: stopped by the wall clock without reaching the CPU limit, twice"
)


def _ubsan_kind(message: str) -> str:
    m = message.lower()
    if "signed integer overflow" in m:
        return "signed-integer-overflow"
    if "out of bounds" in m:
        return "index-out-of-bounds"
    if "division by zero" in m:
        return "division-by-zero"
    if "shift" in m:
        return "shift"
    if "null pointer" in m:
        return "null-pointer"
    if "not a valid value" in m:
        return "invalid-value"
    return "undefined-behaviour"


def sanitizer_finding(stderr: str) -> SanitizerFinding | None:
    """The first sanitizer report in a run's stderr, if any.

    Leak reports are ignored: leaks do not make the program's output unreliable.
    """
    if m := _ASAN.search(stderr):
        line = stderr[m.start() :].splitlines()[0]
        return SanitizerFinding(tool="asan", kind=m.group(1), message=line[:300])
    if m := _UBSAN.search(stderr):
        return SanitizerFinding(
            tool="ubsan", kind=_ubsan_kind(m.group(1)), message=m.group(0)[:300]
        )
    return None


class TestReliability(BaseModel):
    __test__ = False
    model_config = ConfigDict(frozen=True)

    test_key: str
    excluded_reason: str | None
    finding: SanitizerFinding | None = None
    repeat_signatures: tuple[Signature, ...] = ()


def assess(
    standard: Mapping[str, RunResult],
    repeats: Mapping[str, Sequence[RunResult]],
    sanitized: Mapping[str, RunResult] | None,
) -> dict[str, TestReliability]:
    """Combine the evidence channels for each test key in `standard`.

    `repeats` holds extra standard-build runs (typically only for failing tests);
    `sanitized` is None when the sanitizer build was unavailable.
    """
    out: dict[str, TestReliability] = {}
    for key, first in standard.items():
        sig = signature_of(first)
        again = tuple(signature_of(r) for r in repeats.get(key, ()))
        finding = None
        if sanitized is not None and key in sanitized:
            finding = sanitizer_finding(sanitized[key].stderr)
        reason: str | None = None
        if finding is not None:
            reason = f"sanitizer: {finding.kind}"
        elif sig.kind is OutcomeKind.INCONCLUSIVE:
            reason = INCONCLUSIVE_REASON
        elif any(s != sig for s in again):
            reason = "non-deterministic: repeated run produced a different outcome"
        out[key] = TestReliability(
            test_key=key, excluded_reason=reason, finding=finding, repeat_signatures=again
        )
    return out
