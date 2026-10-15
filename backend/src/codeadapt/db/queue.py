"""Database-backed job queue (ADR-004).

Claiming uses an optimistic conditional UPDATE, which is safe for concurrent workers on
both PostgreSQL and SQLite: exactly one worker's UPDATE matches the expected prior state.
Expired leases (a worker died mid-job) are reclaimed; a job that keeps failing for
infrastructure reasons is marked FAILED after `max_attempts`.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import and_, or_, select, update
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


def finish(session: Session, job: Job, *, state: JobState, error: str | None = None) -> None:
    session.execute(
        update(Job)
        .where(Job.id == job.id)
        .values(state=state.value, last_error=error, lease_until=None, updated_at=utcnow())
    )
    session.commit()


def requeue(session: Session, job: Job, error: str) -> None:
    """Infrastructure failure: let another attempt (or worker) try again."""
    session.execute(
        update(Job)
        .where(Job.id == job.id)
        .values(
            state=JobState.QUEUED.value, last_error=error, lease_until=None, updated_at=utcnow()
        )
    )
    session.commit()
