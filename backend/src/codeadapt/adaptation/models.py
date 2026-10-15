"""Inputs and outputs of the adaptive policy (pure data; see docs/methodology.md §5)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from codeadapt.diagnosis.models import Outcome


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TestStatus(StrEnum):
    __test__ = False

    PASSED = "passed"  # reliable and matched the reference
    FAILED = "failed"  # reliable and differed from the reference
    EXCLUDED = "excluded"  # not usable as evidence (sanitizer finding, non-determinism, ...)


class AttemptRecord(_Frozen):
    """One diagnosed submission, reduced to what the policy and the evaluation use."""

    submission_id: str
    problem_slug: str
    created_at: datetime
    outcome: Outcome
    selected_model: str | None = None
    candidates: tuple[str, ...] = ()
    # Empty when nothing ran (compile or execution error).
    tests: dict[str, TestStatus] = Field(default_factory=dict)


class ProbeEvidence(_Frozen):
    """One test outcome attributed to one skill through the problem's probe mapping."""

    skill: str
    problem_slug: str
    test_key: str
    submission_id: str
    status: TestStatus


class Rule(StrEnum):
    """Which row of the methodology §5 table produced a recommendation."""

    HYPOTHESIS_SUPPORTED = "hypothesis_supported"
    AMBIGUOUS = "ambiguous"
    NO_FAILURE_OBSERVED = "no_failure_observed"
    ABSTAINED = "abstained"  # unmodelled, insufficient or unreliable evidence
    NOT_EVALUATED = "not_evaluated"  # compile or execution error


class Action(StrEnum):
    NEW_PROBLEM = "new_problem"
    RETRY = "retry"
    NONE = "none"  # nothing left to recommend in the family


class SuccessCriterion(_Frozen):
    """What a follow-up attempt must show, fixed when the recommendation is made."""

    # Every reliable follow-up test that probes one of these skills must pass.
    skills: tuple[str, ...]
    # And the follow-up must not be diagnosed with an error model of one of these skills.
    excluded_model_skills: tuple[str, ...] = ()
    text: str


class Recommendation(_Frozen):
    policy: str
    policy_version: str
    rule: Rule
    action: Action
    problem_slug: str | None
    target_skills: tuple[str, ...] = ()
    # None means no success is claimed for the follow-up (methodology §5).
    criterion: SuccessCriterion | None = None
    # Abstentions are flagged so a researcher can look at what the method could not explain.
    review_flag: bool = False
    rationale: dict[str, Any] = Field(default_factory=dict)


class Verdict(StrEnum):
    CRITERION_MET = "criterion_met"
    CRITERION_NOT_MET = "criterion_not_met"
    NOT_COMPARABLE = "not_comparable"


class ProbeResult(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    EXCLUDED = "excluded"
    NOT_PROBED = "not_probed"


class ProbeComparison(_Frozen):
    probe: str
    skills: tuple[str, ...]
    index: ProbeResult
    followup: ProbeResult


class FollowupEvaluation(_Frozen):
    method: str
    method_version: str
    verdict: Verdict
    reason: str
    # Counts over the follow-up tests that probe a target skill.
    passed: int = 0
    failed: int = 0
    excluded: int = 0
    probes: tuple[ProbeComparison, ...] = ()
