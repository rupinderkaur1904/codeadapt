"""Database-backed job queue (ADR-004).

Claiming uses an optimistic conditional UPDATE, which is safe for concurrent workers on
both PostgreSQL and SQLite: exactly one worker's UPDATE matches the expected prior state.
Expired leases (a worker died mid-job) are reclaimed; a job that keeps failing for
infrastructure reasons is marked FAILED after `max_attempts`.

`finish` and `requeue` are fenced: they change the job only while it is still this claim
(same worker, same attempt, still running). A worker whose lease expired and whose job was
reclaimed by another worker therefore cannot overwrite the newer attempt's state.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import ColumnElement, and_, or_, select, update
from sqlalchemy.orm import Session

from codeadapt.db.models import Job, JobState, utcnow


def claim_next(
    session: Session, worker_id: str, *, lease_seconds: float, max_attempts: int
) -> Job | None:
    now = utcnow()
    claimable = or_(
        Job.state == JobState.QUEUED.value,
        and_(Job.state == JobState.RUNNING.value, Job.lease_until < now),
    )
    for job in session.scalars(select(Job).where(claimable).order_by(Job.id).limit(10)).all():
        if job.attempts >= max_attempts:
            session.execute(
                update(Job)
                .where(Job.id == job.id, Job.state == job.state, Job.attempts == job.attempts)
                .values(
                    state=JobState.FAILED.value,
                    last_error=job.last_error or "lease expired too many times",
                    updated_at=now,
                )
            )
            session.commit()
            continue
        claimed = session.execute(
            update(Job)
            .where(Job.id == job.id, Job.state == job.state, Job.attempts == job.attempts)
            .values(
                state=JobState.RUNNING.value,
                attempts=job.attempts + 1,
                claimed_by=worker_id,
                lease_until=now + timedelta(seconds=lease_seconds),
                updated_at=now,
            )
        )
        session.commit()
        if claimed.rowcount == 1:  # type: ignore[attr-defined]
            session.refresh(job)
            return job
    return None


def _this_claim(job: Job) -> ColumnElement[bool]:
    return and_(
        Job.id == job.id,
        Job.state == JobState.RUNNING.value,
        Job.claimed_by == job.claimed_by,
        Job.attempts == job.attempts,
    )


def finish(session: Session, job: Job, *, state: JobState, error: str | None = None) -> bool:
    """Record the final state; False if the claim was lost (the job was reclaimed)."""
    result = session.execute(
        update(Job)
        .where(_this_claim(job))
        .values(state=state.value, last_error=error, lease_until=None, updated_at=utcnow())
    )
    session.commit()
    return bool(result.rowcount == 1)  # type: ignore[attr-defined]


def requeue(session: Session, job: Job, error: str) -> bool:
    """Infrastructure failure: let another attempt (or worker) try again.

    False if the claim was lost (the job was reclaimed).
    """
    result = session.execute(
        update(Job)
        .where(_this_claim(job))
        .values(
            state=JobState.QUEUED.value, last_error=error, lease_until=None, updated_at=utcnow()
        )
    )
    session.commit()
    return bool(result.rowcount == 1)  # type: ignore[attr-defined]
