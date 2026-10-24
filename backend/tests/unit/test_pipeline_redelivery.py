"""A redelivered job whose submission is already diagnosed is not run again (no Docker)."""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import (
    DiagnosisRow,
    Environment,
    ExecutionRun,
    Job,
    JobState,
    RecommendationRow,
    utcnow,
)
from codeadapt.diagnosis import FingerprintConsistencyV1
from codeadapt.worker.pipeline import Pipeline
from tests.paths import DEMO_CONTENT
from tests.unit.test_queue import claim, enqueue


class NoSandbox:
    """Any use of the sandbox fails the test: a redelivered job must not execute anything."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"sandbox.{name} used for an already diagnosed submission")


def record_diagnosis(sessions: sessionmaker[Session], job_id: int, method: Any) -> None:
    with sessions() as s:
        job = s.get_one(Job, job_id)
        env = Environment(digest="e" * 64, info={})
        s.add(env)
        s.flush()
        now = utcnow()
        run = ExecutionRun(
            submission_id=job.submission_id,
            environment_id=env.id,
            profile="standard",
            compile_status="ok",
            compile_flags=[],
            compile_exit_code=0,
            compile_diagnostics="",
            compile_diagnostics_truncated=False,
            compile_wall_ms=1,
            started_at=now,
            finished_at=now,
        )
        s.add(run)
        s.flush()
        s.add(
            DiagnosisRow(
                submission_id=job.submission_id,
                run_id=run.id,
                fingerprint_set_id=None,
                method=method.name,
                method_version=method.version,
                outcome="no_failure",
                selected_model=None,
                candidates=[],
                support=0,
                rationale={},
            )
        )
        s.commit()


def test_redelivered_job_is_finished_without_running_again(
    sessions: sessionmaker[Session],
) -> None:
    (job_id,) = enqueue(sessions)
    method = FingerprintConsistencyV1()
    record_diagnosis(sessions, job_id, method)  # the first worker died after committing this
    job = claim(sessions, "w2")
    assert job is not None
    pipeline = Pipeline(NoSandbox(), sessions, Catalogue.load(DEMO_CONTENT), method)
    asyncio.run(pipeline.handle(job))
    with sessions() as s:
        assert s.get_one(Job, job_id).state == JobState.DONE.value
        assert s.scalar(select(func.count()).select_from(DiagnosisRow)) == 1
        assert s.scalar(select(func.count()).select_from(RecommendationRow)) == 0


def test_other_method_version_does_not_count_as_done(sessions: sessionmaker[Session]) -> None:
    (job_id,) = enqueue(sessions)
    record_diagnosis(sessions, job_id, FingerprintConsistencyV1(version="1.2"))
    job = claim(sessions, "w2")
    assert job is not None
    pipeline = Pipeline(
        NoSandbox(),
        sessions,
        Catalogue.load(DEMO_CONTENT),
        FingerprintConsistencyV1(),
    )
    asyncio.run(pipeline.handle(job))  # runs, so touches the sandbox, so the job fails
    with sessions() as s:
        row = s.get_one(Job, job_id)
        assert row.state == JobState.FAILED.value
        assert "sandbox." in (row.last_error or "")
