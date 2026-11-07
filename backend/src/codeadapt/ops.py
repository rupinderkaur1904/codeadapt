"""Operational status for monitoring (ADR-042): queue health, failures, schema revision.

The status holds counts and ages only: no usernames, source, or error text, so it can be
printed to a cron log or an uptime checker without exposing learner data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from codeadapt.db import migrate
from codeadapt.db.models import Job, JobState
from codeadapt.db.session import as_utc
from codeadapt.worker.recovery import ADAPTATION_FAILED, ADAPTATION_RECOVERED


@dataclass(frozen=True)
class Thresholds:
    max_queue_age_seconds: float = 300.0  # a student has waited 5 minutes for a result
    max_failed_jobs: int = 0  # infrastructure failures in the window
    max_adaptation_failures: int = 0  # diagnoses delivered without a recommendation (D6)


@dataclass(frozen=True)
class Status:
    window_hours: float
    queued: int
    running: int
    running_with_expired_lease: int
    oldest_queued_seconds: float | None
    failed_in_window: int
    adaptation_failures_in_window: int
    adaptation_recovered_in_window: int
    done_in_window: int
    schema_revision: str | None
    expected_schema_revision: str | None

    def problems(self, limits: Thresholds) -> list[str]:
        found: list[str] = []
        if self.schema_revision != self.expected_schema_revision:
            found.append("database schema is not at the code's migration head")
        if (
            self.oldest_queued_seconds is not None
            and self.oldest_queued_seconds > limits.max_queue_age_seconds
        ):
            found.append(
                f"oldest queued job waited {self.oldest_queued_seconds:.0f} s "
                f"(limit {limits.max_queue_age_seconds:.0f} s): is a worker running?"
            )
        if self.running_with_expired_lease:
            found.append(f"{self.running_with_expired_lease} running job(s) lost their worker")
        if self.failed_in_window > limits.max_failed_jobs:
            found.append(f"{self.failed_in_window} job(s) failed in the window")
        if self.adaptation_failures_in_window > limits.max_adaptation_failures:
            found.append(
                f"{self.adaptation_failures_in_window} diagnosis(es) had no recommendation "
                "because adaptation failed"
            )
        return found

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def collect(session: Session, now: datetime, window_hours: float = 24.0) -> Status:
    since = now - timedelta(hours=window_hours)

    def count(*where: object) -> int:
        return session.scalar(select(func.count()).select_from(Job).where(*where)) or 0  # type: ignore[arg-type]

    oldest = session.scalar(select(func.min(Job.created_at)).where(Job.state == JobState.QUEUED))
    return Status(
        window_hours=window_hours,
        queued=count(Job.state == JobState.QUEUED),
        running=count(Job.state == JobState.RUNNING),
        running_with_expired_lease=count(Job.state == JobState.RUNNING, Job.lease_until < now),
        oldest_queued_seconds=(
            round((now - as_utc(oldest)).total_seconds(), 1) if oldest is not None else None
        ),
        failed_in_window=count(Job.state == JobState.FAILED, Job.updated_at >= since),
        adaptation_failures_in_window=count(
            Job.state == JobState.DONE,
            Job.updated_at >= since,
            # A failure a learner's retry later recovered still happened: count it.
            or_(
                Job.last_error.like(ADAPTATION_FAILED + "%"),
                Job.last_error.like(ADAPTATION_RECOVERED + "%"),
            ),
        ),
        adaptation_recovered_in_window=count(
            Job.state == JobState.DONE,
            Job.updated_at >= since,
            Job.last_error.like(ADAPTATION_RECOVERED + "%"),
        ),
        done_in_window=count(Job.state == JobState.DONE, Job.updated_at >= since),
        schema_revision=migrate.current_revision(session.connection()),
        expected_schema_revision=migrate.head_revision(),
    )


def database_fingerprint(session: Session) -> dict[str, object]:
    """Schema revision, row count and a SHA-256 of every table's rows in primary-key order.

    Run against a source database and its restored copy: equal fingerprints mean the
    restore reproduced every row (M3.5). Prints digests only, never row contents.
    """
    import hashlib
    import json

    from codeadapt.db.models import Base

    tables: dict[str, dict[str, object]] = {}
    for table in Base.metadata.sorted_tables:
        order = list(table.primary_key.columns) or list(table.columns)
        digest = hashlib.sha256()
        count = 0
        for row in session.execute(select(table).order_by(*order)):
            digest.update(json.dumps(list(row), default=str, sort_keys=True).encode())
            digest.update(b"\n")
            count += 1
        tables[table.name] = {"rows": count, "sha256": digest.hexdigest()}
    return {"schema_revision": migrate.current_revision(session.connection()), "tables": tables}


def purge_dead_sessions(
    session: Session, now: datetime, older_than_days: float, apply: bool
) -> int:
    """Login sessions that expired or were revoked more than ``older_than_days`` ago.

    They can never authenticate again; they only hold token hashes, CSRF values and
    timestamps. Without ``apply`` nothing is deleted (dry run). Learner and research data
    and the audit log are never touched; their retention is an owner decision
    (docs/pilot/data-governance.md).
    """
    from sqlalchemy import delete, or_

    from codeadapt.db.models import AuthSession

    cutoff = now - timedelta(days=older_than_days)
    dead = or_(AuthSession.expires_at < cutoff, AuthSession.revoked_at < cutoff)
    count = session.scalar(select(func.count()).select_from(AuthSession).where(dead)) or 0
    if apply and count:
        session.execute(delete(AuthSession).where(dead))
        session.commit()
    return count


def erase_learner(session: Session, user_id: int, apply: bool) -> dict[str, int]:
    """Every row that belongs to one account, children first (participant withdrawal,
    docs/pilot/data-governance.md §7). Returns row counts per table.

    Without ``apply`` nothing is deleted (dry run). Shared rows (content versions,
    environments, fingerprints) are not the learner's and are kept. Aggregate results
    already computed outside the database are not affected.
    """
    from sqlalchemy import delete, or_

    from codeadapt.db.models import (
        AuditEvent,
        AuthSession,
        DiagnosisRow,
        ExecutionRun,
        FollowupEvaluationRow,
        RecommendationRow,
        Submission,
        TestObservation,
        User,
    )

    user = session.get(User, user_id)
    if user is None:
        raise LookupError(f"no user with id {user_id}")
    subs = select(Submission.id).where(Submission.user_id == user_id)
    recs = select(RecommendationRow.id).where(RecommendationRow.user_id == user_id)
    runs = select(ExecutionRun.id).where(ExecutionRun.submission_id.in_(subs))
    plan = (
        (
            FollowupEvaluationRow,
            or_(
                FollowupEvaluationRow.recommendation_id.in_(recs),
                FollowupEvaluationRow.submission_id.in_(subs),
            ),
        ),
        (RecommendationRow, RecommendationRow.user_id == user_id),
        (DiagnosisRow, DiagnosisRow.submission_id.in_(subs)),
        (TestObservation, TestObservation.run_id.in_(runs)),
        (ExecutionRun, ExecutionRun.submission_id.in_(subs)),
        (Job, Job.submission_id.in_(subs)),
        (Submission, Submission.user_id == user_id),
        (AuthSession, AuthSession.user_id == user_id),
        (
            AuditEvent,
            or_(
                AuditEvent.user_id == user_id,
                func.lower(AuditEvent.username) == func.lower(user.username),
            ),
        ),
        (User, User.id == user_id),
    )
    counts: dict[str, int] = {}
    for table, where in plan:
        counts[table.__tablename__] = (
            session.scalar(select(func.count()).select_from(table).where(where)) or 0
        )
        if apply:
            session.execute(delete(table).where(where))
    if apply:
        session.commit()
    return counts
