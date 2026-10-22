"""HTTP contracts. Student-facing models are explicit allow-lists: hidden inputs, expected
outputs, error-model keys and fingerprints have no field here, so they cannot leak."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from codeadapt.learner import LearnerEstimate

MAX_SOURCE_BYTES = 64 * 1024


class _Out(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProblemSummary(_Out):
    slug: str
    title: str
    family: str
    # True when the current user has an attempt on this problem with no failing test.
    no_failure_observed: bool = False


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
    # The recommendation made after this submission, and the evaluation of the
    # recommendation this submission followed (if any).
    recommendation: dict[str, Any] | None = None
    followup_evaluation: dict[str, Any] | None = None


class RecommendationAction(StrEnum):
    NEW_PROBLEM = "new_problem"
    RETRY = "retry"
    NONE = "none"


class FollowupVerdict(StrEnum):
    CRITERION_MET = "criterion_met"
    CRITERION_NOT_MET = "criterion_not_met"
    NOT_COMPARABLE = "not_comparable"


class RecommendationView(_Out):
    action: RecommendationAction
    problem_slug: str | None
    problem_title: str | None
    message: str
    # Student-facing descriptions of the targeted skills (never error-model keys).
    focus: list[str]
    based_on_submission_id: str
    created_at: datetime


class FollowupView(_Out):
    verdict: FollowupVerdict
    problem_slug: str
    problem_title: str
    message: str
    submission_id: str
    created_at: datetime


class LearnerNext(_Out):
    recommendation: RecommendationView | None
    last_followup: FollowupView | None


class ResearchSubmissionRow(_Out):
    """Researcher-only: one submission with its latest diagnosis and adaptation output."""

    id: str
    created_at: datetime
    username: str
    data_class: str
    origin: str
    problem_slug: str
    status: SubmissionStatus
    outcome: str | None
    selected_model: str | None
    support: int | None
    recommendation_rule: str | None
    recommended_problem: str | None
    review_flag: bool
    followup_verdict: str | None


class ResearchMetrics(_Out):
    """Researcher-only operational counts. There is no ground truth here, so no accuracy."""

    data_class: str | None
    submissions: int
    outcomes: dict[str, int]
    outcomes_by_problem: dict[str, dict[str, int]]
    recommendations_by_rule: dict[str, int]
    flagged_for_review: int
    followup_verdicts: dict[str, int]


class LearnerModelView(_Out):
    """Researcher-only LM1 output for one learner and one data class (ADR-025).

    Estimates are "estimated under assumed parameters": not fitted, not calibrated, never
    shown to the learner and not used by any policy.
    """

    username: str
    data_class: str
    attempts: int
    estimate: LearnerEstimate


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=1024)


class AuthUser(_Out):
    username: str
    role: str
    # Echo in the X-CSRF-Token header on every state-changing request. None for the
    # development stub, which has no session.
    csrf_token: str | None
