"""LM1: standard Bayesian knowledge tracing over skill observations (ADR-025).

Researcher-only. The estimates are not shown to students and no policy reads them.

The input is `skill_observations()` and nothing else, so everything the evidence layer
excludes (abstentions, qualified diagnoses, unreliable or infrastructure-affected runs,
compile errors) never reaches the model. On top of that, LM1 counts only the first
reliably evaluated attempt on each problem version (owner decision L1): a later attempt on
the same version is a retry after feedback and stays visible as uncounted.

The parameters are assumptions, not fitted or calibrated values, and standard BKT assumes
independent skills, no forgetting, and the same parameters for every problem. None of this
has been checked against real learners.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from codeadapt.adaptation.ledger import SkillMaps, skill_observations
from codeadapt.adaptation.models import AttemptRecord, SkillObservation
from codeadapt.content.models import ProblemSpec
from codeadapt.diagnosis.models import Outcome

MODEL = "bkt-standard"
MODEL_VERSION = "1"
LABEL = "estimated under assumed parameters"
ASSUMPTIONS = (
    "parameters are assumed, not fitted to or calibrated on learner data",
    "skills are independent of each other",
    "no forgetting",
    "the same parameters for every problem",
    "observations come from author-written tests and an author-assigned skill map",
)
# Display threshold only: below it no estimate is shown. Meeting it says nothing about
# whether the estimate is accurate.
MIN_OBSERVATIONS = 3
MIN_PROBLEMS = 2

# Attempts that were not reliably evaluated: they do not use up the counted attempt.
NOT_EVALUATED = frozenset(
    {Outcome.COMPILE_ERROR, Outcome.EXECUTION_ERROR, Outcome.UNRELIABLE_EVIDENCE}
)
RETRY_REASON = "retry: not the first reliably evaluated attempt on this problem version"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class BktParams(_Frozen):
    name: str
    p_init: float  # P(L0)
    p_learn: float  # P(T)
    p_guess: float  # P(G)
    p_slip: float  # P(S)

    @model_validator(mode="after")
    def _check(self) -> BktParams:
        for field in ("p_init", "p_learn", "p_guess", "p_slip"):
            value = getattr(self, field)
            if not 0.0 < value < 1.0:
                raise ValueError(f"{field} must be strictly between 0 and 1, got {value}")
        # Non-degeneracy: otherwise a correct answer could lower the estimate.
        if self.p_guess >= 0.5 or self.p_slip >= 0.5:
            raise ValueError("p_guess and p_slip must both be below 0.5")
        return self


# The author's placeholder values (approved as assumptions on 2026-10-17). Not derived from
# data or from a validated source.
ASSUMED_PARAMS_1 = BktParams(
    name="bkt-params-assumed-1", p_init=0.3, p_learn=0.1, p_guess=0.2, p_slip=0.1
)


def posterior(p_known: float, correct: bool, params: BktParams) -> float:
    """P(known | observation), before the learn transition."""
    if correct:
        known = p_known * (1 - params.p_slip)
        unknown = (1 - p_known) * params.p_guess
    else:
        known = p_known * params.p_slip
        unknown = (1 - p_known) * (1 - params.p_guess)
    return known / (known + unknown)


def update(p_known: float, correct: bool, params: BktParams) -> float:
    """One BKT step: condition on the observation, then apply the learn transition."""
    p = posterior(p_known, correct, params)
    return p + (1 - p) * params.p_learn


class TracedObservation(_Frozen):
    observation: SkillObservation
    counted: bool
    reason: str | None = None  # why an observation was not counted
    p_known_after: float | None = None  # only for counted observations


class SkillEstimate(_Frozen):
    skill: str
    state: Literal["estimated", "insufficient_data"]
    # P(known) after the last counted observation and its learn transition. None below the
    # display threshold.
    p_known: float | None
    counted: int
    distinct_problems: int  # by problem identity (slug), not by content version
    observations: tuple[TracedObservation, ...]


class LearnerEstimate(_Frozen):
    model: str = MODEL
    model_version: str = MODEL_VERSION
    parameter_set: str
    label: str = LABEL
    assumptions: tuple[str, ...] = ASSUMPTIONS
    min_observations: int = MIN_OBSERVATIONS
    min_problems: int = MIN_PROBLEMS
    skills: tuple[SkillEstimate, ...]


def _ordered(attempts: Sequence[AttemptRecord]) -> list[AttemptRecord]:
    return sorted(attempts, key=lambda a: (a.created_at, a.submission_id))


def counted_attempts(attempts: Sequence[AttemptRecord]) -> set[str]:
    """Submission ids whose observations count: the first reliably evaluated attempt per
    (problem, content version). Attempts that were not reliably evaluated do not use it up.
    """
    first: dict[tuple[str, str | None], str] = {}
    for a in _ordered(attempts):
        if a.outcome in NOT_EVALUATED:
            continue
        first.setdefault((a.problem_slug, a.problem_version), a.submission_id)
    return set(first.values())


def estimate(
    attempts: Sequence[AttemptRecord],
    problems: Mapping[str, ProblemSpec],
    skill_maps: SkillMaps | None = None,
    params: BktParams = ASSUMED_PARAMS_1,
) -> LearnerEstimate:
    """Trace every observed skill of one learner (one data class) through BKT."""
    counted_ids = counted_attempts(attempts)
    by_skill: dict[str, list[SkillObservation]] = {}
    for obs in skill_observations(_ordered(attempts), problems, skill_maps):
        by_skill.setdefault(obs.skill, []).append(obs)

    skills = []
    for skill in sorted(by_skill):
        p = params.p_init
        traced = []
        slugs: set[str] = set()
        for obs in by_skill[skill]:
            if obs.submission_id not in counted_ids:
                traced.append(
                    TracedObservation(observation=obs, counted=False, reason=RETRY_REASON)
                )
                continue
            p = update(p, obs.value == "correct", params)
            slugs.add(obs.problem_slug)
            traced.append(TracedObservation(observation=obs, counted=True, p_known_after=p))
        counted = sum(t.counted for t in traced)
        enough = counted >= MIN_OBSERVATIONS and len(slugs) >= MIN_PROBLEMS
        skills.append(
            SkillEstimate(
                skill=skill,
                state="estimated" if enough else "insufficient_data",
                p_known=p if enough else None,
                counted=counted,
                distinct_problems=len(slugs),
                observations=tuple(traced),
            )
        )
    return LearnerEstimate(parameter_set=params.name, skills=tuple(skills))
