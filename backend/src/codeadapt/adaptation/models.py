"""Inputs and outputs of the adaptive policy (pure data; see docs/methodology.md §5)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

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
    # The content version the attempt was diagnosed against; skills are attributed with
    # that version's skill map (ADR-023, D4). None only for synthetic trajectories.
    problem_version: str | None = None
    selected_model: str | None = None
    candidates: tuple[str, ...] = ()
    # A supported diagnosis the method qualified (one behaviour group), or whose model
    # documents a known collision. The policy passes this on; it never strengthens it.
    qualified: bool = False
    # Empty when nothing ran (compile or execution error).
    tests: dict[str, TestStatus] = Field(default_factory=dict)


class ProbeEvidence(_Frozen):
    """One test outcome attributed to one skill (see ledger.build_ledger for the rules)."""

    skill: str
    problem_slug: str
    test_key: str
    submission_id: str
    status: TestStatus
    # For a failure: the error model whose supported diagnosis explains it.
    explained_by: str | None = None


class SkillObservation(_Frozen):
    """One attempt's evidence about one skill: the learner-model input (ADR-023, D3).

    `incorrect` means an unqualified supported diagnosis selected an error model of this
    skill; `correct` means every reliable test probing the skill passed. Neither is a
    statement about mastery or about what the learner was thinking.
    """

    skill: str
    value: Literal["correct", "incorrect"]
    basis: str
    submission_id: str
    problem_slug: str
    problem_version: str | None
    created_at: datetime
    test_keys: tuple[str, ...]
    # 1 for the learner's first attempt on this problem, 2 for the next, ... A retry is not
    # independent of the earlier attempt: the learner has seen which tests failed.
    attempt_ordinal: int


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


class Relation(StrEnum):
    """What kind of evidence a follow-up is, by how its problem relates to the index's.

    None of these is evidence of mastery. `transfer` only says the follow-up problem is
    linked as a transfer problem in the curriculum; one passing attempt there is a single
    observation, not demonstrated transfer.
    """

    SAME_PROBLEM = "same_problem"  # a retry: the student has already seen these tests fail
    EQUIVALENT_PRACTICE = "equivalent_practice"  # linked equivalent, or same family
    TRANSFER = "transfer"  # linked as a transfer problem
    OTHER = "other"


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
    relation: Relation = Relation.OTHER
