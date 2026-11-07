"""What a learner sees after adaptation fails, and a safe retry of it (ADR-042, D6).

When the policy step fails after a diagnosis was committed, the worker finishes the job
DONE with ``jobs.last_error = "adaptation failed: ..."``. The learner's latest stored
recommendation then predates an attempt the policy never saw, so it may be stale. The
owner's decision (2026-11-07):

- show a neutral fallback message instead of any recommendation or follow-up verdict;
- keep the learner's previous work (submissions and diagnoses are never touched);
- log the internal error (the worker does, and so does a failed retry);
- let the learner retry, and make a retry unable to duplicate any state change.

A retry calls the unchanged, research-frozen ``adapt`` on the same submission and diagnosis.
It is allowed only while that submission is the learner's newest one, so the policy sees
exactly the attempt history it would have seen the first time. Exactly one retry can claim
a failure: the claim is a conditional UPDATE of the job's marker, committed in the same
transaction as the recommendation. A second or concurrent retry finds nothing to claim.
"""

from __future__ import annotations

import enum
import logging

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from codeadapt.adaptation import PolicyV1
from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import DiagnosisRow, Job, JobState, RecommendationRow, Submission
from codeadapt.logs import redact
from codeadapt.worker.adapt import adapt

log = logging.getLogger(__name__)

# Prefix of `jobs.last_error` on a DONE job whose diagnosis was recorded but whose
# adaptation step failed. Ops status counts these.
ADAPTATION_FAILED = "adaptation failed: "
# The same failure after a learner's retry produced the adaptation output. The original
# error text is kept after the prefix, and ops status still counts it as a failure.
ADAPTATION_RECOVERED = "adaptation recovered by retry; was: "


class RetryResult(enum.StrEnum):
    RECOVERED = "recovered"  # adaptation ran and its output is stored
    NOT_NEEDED = "not_needed"  # nothing to retry (or another retry already did it)
    SUPERSEDED = "superseded"  # a newer submission exists; its own adaptation applies
    FAILED = "failed"  # adaptation failed again; the fallback message stays


def pending_failure(session: Session, user_id: int) -> Job | None:
    """The learner's newest adaptation failure that leaves their recommendation stale.

    A failure is pending when its submission is newer than the submission that produced
    the learner's latest recommendation (or the learner has no recommendation at all).
    """
    latest_source = session.scalar(
        select(Submission.created_at)
        .join(RecommendationRow, RecommendationRow.submission_id == Submission.id)
        .where(RecommendationRow.user_id == user_id)
        .order_by(RecommendationRow.id.desc())
        .limit(1)
    )
    query = (
        select(Job)
        .join(Submission, Submission.id == Job.submission_id)
        .where(
            Submission.user_id == user_id,
            Job.state == JobState.DONE.value,
            Job.last_error.like(ADAPTATION_FAILED + "%"),
        )
    )
    if latest_source is not None:
        query = query.where(Submission.created_at > latest_source)
    return session.scalars(query.order_by(Submission.created_at.desc()).limit(1)).first()


def retry_adaptation(
    session: Session, user_id: int, catalogue: Catalogue, policy: PolicyV1
) -> RetryResult:
    """Re-run adaptation for the learner's pending failure, at most once. Commits."""
    job = pending_failure(session, user_id)
    if job is None:
        return RetryResult.NOT_NEEDED
    submission = session.get_one(Submission, job.submission_id)
    newer = session.scalar(
        select(Submission.id)
        .where(Submission.user_id == user_id, Submission.created_at > submission.created_at)
        .limit(1)
    )
    if newer is not None:
        return RetryResult.SUPERSEDED
    diagnosis = session.scalars(
        select(DiagnosisRow)
        .where(DiagnosisRow.submission_id == submission.id)
        .order_by(DiagnosisRow.id.desc())
        .limit(1)
    ).first()
    if diagnosis is None:  # cannot happen for a DONE job with the marker; be safe
        return RetryResult.NOT_NEEDED

    marker = job.last_error or ""
    claimed = session.execute(
        update(Job)
        .where(Job.id == job.id, Job.last_error == marker)
        .values(
            last_error=ADAPTATION_RECOVERED + marker.removeprefix(ADAPTATION_FAILED),
            updated_at=job.updated_at,  # keep the failure inside its status window
        )
        .execution_options(synchronize_session=False)
    )
    if claimed.rowcount != 1:  # type: ignore[attr-defined]
        session.rollback()  # another retry claimed it first
        return RetryResult.NOT_NEEDED
    try:
        adapt(session, submission, diagnosis, catalogue, policy)
        session.commit()
    except Exception as exc:
        session.rollback()  # the marker and every adaptation row go back as they were
        log.error(
            "adaptation retry failed for submission %s: %s",
            submission.id,
            redact(f"{type(exc).__name__}: {exc}")[:2000],
            extra={"event": "adaptation_retry_failed", "submission_id": submission.id},
        )
        return RetryResult.FAILED
    log.info(
        "adaptation recovered by retry for submission %s",
        submission.id,
        extra={"event": "adaptation_recovered", "submission_id": submission.id},
    )
    return RetryResult.RECOVERED
