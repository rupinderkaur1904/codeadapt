"""Infrastructure failures and redelivery leave no evidence behind (no Docker).

An unavailable sandbox is an infrastructure fault, not a property of the student's code: the
job is requeued, then failed after its attempts run out, and at no point is a run, diagnosis,
recommendation or learner-model attempt recorded. A redelivered job adds no second attempt.
"""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, sessionmaker

from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import (
    DiagnosisRow,
    ExecutionRun,
    Job,
    JobState,
    RecommendationRow,
    Submission,
)
from codeadapt.diagnosis import FingerprintConsistencyV1
from codeadapt.execution.backend import SandboxUnavailableError
from codeadapt.worker.adapt import learner_attempts
from codeadapt.worker.pipeline import Pipeline
from tests.paths import DEMO_CONTENT
from tests.unit.test_pipeline_redelivery import NoSandbox, record_diagnosis
from tests.unit.test_queue import claim, enqueue


class UnavailableSandbox:
    """Every use of the sandbox fails as if the container runtime were down."""

    def __getattr__(self, name: str) -> Any:
        raise SandboxUnavailableError(f"runtime down (sandbox.{name})")


def counts(sessions: sessionmaker[Session]) -> dict[str, int]:
    with sessions() as s:
        return {
            table.__name__: s.scalar(select(func.count()).select_from(table)) or 0
            for table in (ExecutionRun, DiagnosisRow, RecommendationRow)
        }


def attempts_of(sessions: sessionmaker[Session], job_id: int) -> int:
    with sessions() as s:
        sub = s.get_one(Submission, s.get_one(Job, job_id).submission_id)
        return len(learner_attempts(s, sub.user_id, sub.data_class))


def test_unavailable_sandbox_requeues_then_fails_and_records_no_evidence(
    sessions: sessionmaker[Session],
) -> None:
    (job_id,) = enqueue(sessions)
    pipeline = Pipeline(
        UnavailableSandbox(), sessions, Catalogue.load(DEMO_CONTENT), FingerprintConsistencyV1()
    )
    for _ in range(3):
        job = claim(sessions)
        assert job is not None
        asyncio.run(pipeline.handle(job))
        with sessions() as s:
            row = s.get_one(Job, job_id)
            assert row.state == JobState.QUEUED.value
            assert "sandbox unavailable" in (row.last_error or "")
    # Attempts exhausted: the job is failed by the queue, never diagnosed.
    assert claim(sessions) is None
    with sessions() as s:
        assert s.get_one(Job, job_id).state == JobState.FAILED.value
    assert counts(sessions) == {"ExecutionRun": 0, "DiagnosisRow": 0, "RecommendationRow": 0}
    assert attempts_of(sessions, job_id) == 0


def test_redelivery_adds_no_second_learner_attempt(sessions: sessionmaker[Session]) -> None:
    (job_id,) = enqueue(sessions)
    method = FingerprintConsistencyV1()
    record_diagnosis(sessions, job_id, method)
    with sessions() as s:  # the shared helper stores a placeholder outcome; use a real one
        s.execute(update(DiagnosisRow).values(outcome="no_failure_observed"))
        s.commit()
    assert attempts_of(sessions, job_id) == 1
    for worker in ("w2", "w3"):  # delivered twice more after the first worker died
        with sessions() as s:
            s.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(state=JobState.QUEUED.value, lease_until=None)
            )
            s.commit()
        job = claim(sessions, worker)
        assert job is not None
        asyncio.run(
            Pipeline(NoSandbox(), sessions, Catalogue.load(DEMO_CONTENT), method).handle(job)
        )
    assert attempts_of(sessions, job_id) == 1
    assert counts(sessions)["DiagnosisRow"] == 1
