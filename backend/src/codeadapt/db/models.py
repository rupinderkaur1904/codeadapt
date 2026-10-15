"""Relational schema (docs/architecture.md §4).

Evidence tables (`execution_runs`, `test_observations`, `diagnoses`, `fingerprint_sets`,
`recommendations`, `followup_evaluations`)
are append-only: the application inserts rows and never updates or deletes them. Only
`jobs` carries mutable state.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)
    type_annotation_map: ClassVar[dict[Any, Any]] = {dict[str, Any]: JSON, list[Any]: JSON}


class DataClass(StrEnum):
    """ADR-008: provenance class carried by users and everything derived from them."""

    REAL = "real"
    SYNTHETIC = "synthetic"
    DEV = "dev"


class Role(StrEnum):
    STUDENT = "student"
    RESEARCHER = "researcher"
    ADMIN = "admin"


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"  # infrastructure failure after all attempts; never a student verdict


def _ts() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    role: Mapped[str] = mapped_column(String(16))
    data_class: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = _ts()


class ProblemVersion(Base):
    __tablename__ = "problem_versions"

    version: Mapped[str] = mapped_column(String(64), primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), index=True)
    family: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = _ts()


class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    digest: Mapped[str] = mapped_column(String(64), unique=True)  # sha256 of `info`
    info: Mapped[dict[str, Any]]
    created_at: Mapped[datetime] = _ts()


class FingerprintSetRow(Base):
    __tablename__ = "fingerprint_sets"
    __table_args__ = (UniqueConstraint("problem_version", "environment_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_version: Mapped[str] = mapped_column(ForeignKey("problem_versions.version"))
    environment_id: Mapped[int] = mapped_column(ForeignKey("environments.id"))
    valid: Mapped[bool] = mapped_column(Boolean)
    data: Mapped[dict[str, Any]]  # FingerprintSet
    report: Mapped[dict[str, Any]]  # ValidationReport
    created_at: Mapped[datetime] = _ts()


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_version: Mapped[str] = mapped_column(ForeignKey("problem_versions.version"))
    source: Mapped[str] = mapped_column(Text)
    source_sha256: Mapped[str] = mapped_column(String(64))
    origin: Mapped[str] = mapped_column(String(16))  # student | synthetic | eval
    data_class: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = _ts()

    job: Mapped[Job] = relationship(back_populates="submission", uselist=False)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), unique=True)
    state: Mapped[str] = mapped_column(String(16), index=True, default=JobState.QUEUED.value)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    claimed_by: Mapped[str | None] = mapped_column(String(128))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _ts()
    updated_at: Mapped[datetime] = _ts()

    submission: Mapped[Submission] = relationship(back_populates="job")


class ExecutionRun(Base):
    __tablename__ = "execution_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), index=True)
    environment_id: Mapped[int] = mapped_column(ForeignKey("environments.id"))
    profile: Mapped[str] = mapped_column(String(16))
    compile_status: Mapped[str] = mapped_column(String(32))
    compile_flags: Mapped[list[Any]]
    compile_exit_code: Mapped[int | None] = mapped_column(Integer)
    compile_diagnostics: Mapped[str] = mapped_column(Text)
    compile_diagnostics_truncated: Mapped[bool] = mapped_column(Boolean)
    compile_wall_ms: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TestObservation(Base):
    __tablename__ = "test_observations"
    __test__ = False
    __table_args__ = (UniqueConstraint("run_id", "test_key", "repeat_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("execution_runs.id"), index=True)
    test_key: Mapped[str] = mapped_column(String(64))
    repeat_index: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    signature_kind: Mapped[str] = mapped_column(String(32))
    signature_detail: Mapped[str] = mapped_column(Text)
    exit_code: Mapped[int | None] = mapped_column(Integer)
    signal: Mapped[int | None] = mapped_column(Integer)
    stdout: Mapped[str] = mapped_column(Text)
    stdout_sha256: Mapped[str] = mapped_column(String(64))
    stdout_truncated: Mapped[bool] = mapped_column(Boolean)
    stderr: Mapped[str] = mapped_column(Text)
    stderr_truncated: Mapped[bool] = mapped_column(Boolean)
    wall_ms: Mapped[int] = mapped_column(Integer)
    oom_killed: Mapped[bool] = mapped_column(Boolean)
    timed_out: Mapped[bool] = mapped_column(Boolean)
    excluded_reason: Mapped[str | None] = mapped_column(Text)


class DiagnosisRow(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("execution_runs.id"))
    fingerprint_set_id: Mapped[int | None] = mapped_column(ForeignKey("fingerprint_sets.id"))
    method: Mapped[str] = mapped_column(String(64))
    method_version: Mapped[str] = mapped_column(String(16))
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    selected_model: Mapped[str | None] = mapped_column(String(64))
    candidates: Mapped[list[Any]]
    support: Mapped[int] = mapped_column(Integer)
    rationale: Mapped[dict[str, Any]]
    created_at: Mapped[datetime] = _ts()


class RecommendationRow(Base):
    """Output of the adaptive policy after one diagnosis (append-only).

    A learner's open recommendation is their latest one without a follow-up evaluation.
    """

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), index=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnoses.id"))
    policy: Mapped[str] = mapped_column(String(64))
    policy_version: Mapped[str] = mapped_column(String(16))
    rule: Mapped[str] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(16))
    problem_slug: Mapped[str | None] = mapped_column(String(64))
    target_skills: Mapped[list[Any]]
    criterion: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    review_flag: Mapped[bool] = mapped_column(Boolean)
    rationale: Mapped[dict[str, Any]]
    created_at: Mapped[datetime] = _ts()


class FollowupEvaluationRow(Base):
    """Verdict on the first compiled attempt after a recommendation (append-only)."""

    __tablename__ = "followup_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.id"), unique=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), index=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnoses.id"))
    method: Mapped[str] = mapped_column(String(64))
    method_version: Mapped[str] = mapped_column(String(16))
    verdict: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    passed: Mapped[int] = mapped_column(Integer)
    failed: Mapped[int] = mapped_column(Integer)
    excluded: Mapped[int] = mapped_column(Integer)
    probes: Mapped[list[Any]]
    created_at: Mapped[datetime] = _ts()
