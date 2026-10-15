"""HTTP contracts. Student-facing models are explicit allow-lists: hidden inputs, expected
outputs, error-model keys and fingerprints have no field here, so they cannot leak."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_SOURCE_BYTES = 64 * 1024


class _Out(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProblemSummary(_Out):
    slug: str
    title: str
    family: str


class SampleTest(_Out):
    input: str
    expected_output: str
    description: str


class ProblemDetail(_Out):
    slug: str
    title: str
    version: str
    statement: str
    interface: str
    starter_code: str
    sample_tests: list[SampleTest]


class SubmissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_slug: str = Field(min_length=1, max_length=64)
    source: str = Field(min_length=1)

    @field_validator("source")
    @classmethod
    def _size(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise ValueError(f"source exceeds {MAX_SOURCE_BYTES} bytes")
        return value


class SubmissionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"  # the platform failed, not the student


class TestVerdict(StrEnum):
    PASSED = "passed"
    WRONG_OUTPUT = "wrong_output"
    RUNTIME_ERROR = "runtime_error"
    TIME_LIMIT = "time_limit"
    MEMORY_LIMIT = "memory_limit"
    OUTPUT_LIMIT = "output_limit"
    UNDEFINED_BEHAVIOUR = "undefined_behaviour"  # sanitizer finding: output not trustworthy
    INCONSISTENT = "inconsistent"  # repeated runs disagreed
    NOT_EVALUATED = "not_evaluated"


class TestResultView(_Out):
    __test__ = False

    number: int
    visibility: str
    description: str
    verdict: TestVerdict
    # Only for sample tests:
    input: str | None = None
    expected_output: str | None = None
    actual_output: str | None = None


class FeedbackKind(StrEnum):
    COMPILE_ERROR = "compile_error"
    SYSTEM_ERROR = "system_error"
    INCONSISTENT_BEHAVIOUR = "inconsistent_behaviour"
    ALL_TESTS_PASSED = "all_tests_passed"
    RECOGNISED_PATTERN = "recognised_pattern"
    FAILING_CASES = "failing_cases"


class FeedbackView(_Out):
    kind: FeedbackKind
    message: str
    hint: str | None = None
    related_cases: list[str] = []
    # Undefined behaviour detected by the sanitizer build, phrased for students.
    safety_findings: list[str] = []


class CompileView(_Out):
    ok: bool
    diagnostics: str


class SubmissionView(_Out):
    id: str
    problem_slug: str
    status: SubmissionStatus
    created_at: datetime
    compile: CompileView | None = None
    tests: list[TestResultView] = []
    feedback: FeedbackView | None = None


class SubmissionAccepted(_Out):
    id: str
    status: SubmissionStatus


class TraceView(_Out):
    """Researcher-only: the full evidence chain for one submission."""

    submission: dict[str, Any]
    job: dict[str, Any]
    environment: dict[str, Any] | None
    execution_runs: list[dict[str, Any]]  # standard build first, then the sanitizer build
    observations: list[dict[str, Any]]
    diagnosis: dict[str, Any] | None
    content_validation: dict[str, Any] | None
