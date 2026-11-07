"""ADR-042: readiness, worker lifecycle and heartbeat, warm-up, and the D6 adaptation marker.

No Docker: sandbox-dependent steps are replaced by fakes; the research code paths they call
(fingerprints, diagnosis, policy) are not changed or re-implemented here.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from codeadapt import ops
from codeadapt.adaptation import PolicyV1
from codeadapt.api.app import create_app
from codeadapt.auth import cli as admin
from codeadapt.config import Environment, Settings
from codeadapt.content.catalogue import Catalogue
from codeadapt.db import migrate, queue
from codeadapt.db.models import (
    DiagnosisRow,
    Job,
    JobState,
    RecommendationRow,
    Submission,
    utcnow,
)
from codeadapt.diagnosis import FingerprintConsistencyV1
from codeadapt.worker import main as worker_main
from codeadapt.worker.pipeline import ADAPTATION_FAILED, ContentUnavailableError, Pipeline
from tests.paths import DEMO_CONTENT
from tests.unit.test_pipeline_redelivery import NoSandbox, record_diagnosis
from tests.unit.test_queue import claim, enqueue

# ---------------------------------------------------------------- readiness


def test_ready_when_database_is_at_head(settings: Settings) -> None:
    client = TestClient(create_app(settings))
    r = client.get("/api/v1/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}
    assert migrate.head_revision() is not None


def test_not_ready_when_schema_is_behind(
    settings: Settings, sessions: sessionmaker[Session]
) -> None:
    client = TestClient(create_app(settings, sessions))
    with sessions() as s:
        s.execute(text("UPDATE alembic_version SET version_num = '0005'"))
        s.commit()
    r = client.get("/api/v1/ready")
    assert r.status_code == 503
    assert r.json()["type"].endswith("/not-ready")
    assert "0005" not in r.text  # no internal detail in the answer
    assert client.get("/api/v1/health").status_code == 200  # liveness is unaffected


def test_not_ready_when_database_is_unreachable(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = TestClient(create_app(settings))

    def down(_connection: Any) -> str:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(migrate, "current_revision", down)
    r = client.get("/api/v1/ready")
    assert r.status_code == 503
    assert "refused" not in r.text


def test_ready_is_public_in_production_with_security_headers(
    settings: Settings, sessions: sessionmaker[Session]
) -> None:
    prod = replace(settings, env=Environment.PRODUCTION, allowed_hosts=("testserver",))
    client = TestClient(create_app(prod, sessions), base_url="https://testserver")
    r = client.get("/api/v1/ready")
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"


# ---------------------------------------------------------------- heartbeat


def test_heartbeat_check(tmp_path: Path) -> None:
    beat = tmp_path / "worker.heartbeat"
    assert worker_main.check_heartbeat(beat) == 1  # never started
    beat.touch()
    assert worker_main.check_heartbeat(beat) == 0
    old = time.time() - worker_main.HEARTBEAT_MAX_AGE_SECONDS - 5
    os.utime(beat, (old, old))
    assert worker_main.check_heartbeat(beat) == 1  # stale: hung or dead


def test_heartbeat_task_keeps_the_file_fresh(tmp_path: Path) -> None:
    beat = tmp_path / "worker.heartbeat"

    async def scenario() -> None:
        task = asyncio.create_task(worker_main.heartbeat_file(beat, interval=0.01))
        await asyncio.sleep(0.05)
        task.cancel()

    asyncio.run(scenario())
    assert worker_main.check_heartbeat(beat) == 0


def test_check_command_needs_a_heartbeat_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEADAPT_ENV", "test")
    monkeypatch.delenv("CODEADAPT_WORKER_HEARTBEAT_FILE", raising=False)
    with pytest.raises(SystemExit):
        worker_main.main(["--check"])


# ---------------------------------------------------------------- graceful stop


class FinishingPipeline:
    """Marks each job DONE, as a real pipeline would, and can request a stop mid-job."""

    def __init__(self, sessions: sessionmaker[Session], stop_after: int | None = None) -> None:
        self.sessions, self.stop_after, self.handled = sessions, stop_after, 0
        self.stop = asyncio.Event()

    async def handle(self, job: Job) -> None:
        self.handled += 1
        if self.stop_after is not None and self.handled >= self.stop_after:
            self.stop.set()  # SIGTERM arrives while this job runs
        await asyncio.sleep(0)
        with self.sessions() as s:
            assert queue.finish(s, job, state=JobState.DONE)


def _states(sessions: sessionmaker[Session]) -> list[str]:
    with sessions() as s:
        return list(s.scalars(select(Job.state).order_by(Job.id)))


def test_stop_finishes_the_current_job_and_claims_no_more(
    settings: Settings, sessions: sessionmaker[Session]
) -> None:
    enqueue(sessions, 3)
    fake = FinishingPipeline(sessions, stop_after=1)
    processed = asyncio.run(
        worker_main.serve(fake, sessions, settings, stop=fake.stop)  # type: ignore[arg-type]
    )
    assert processed == 1
    assert _states(sessions) == ["done", "queued", "queued"]  # nothing left half-run


def test_stop_while_idle_exits_promptly(
    settings: Settings, sessions: sessionmaker[Session]
) -> None:
    slow_poll = replace(settings, worker_poll_seconds=30)

    async def scenario() -> int:
        stop = asyncio.Event()
        task = asyncio.create_task(
            worker_main.serve(
                FinishingPipeline(sessions),  # type: ignore[arg-type]
                sessions,
                slow_poll,
                stop=stop,
            )
        )
        await asyncio.sleep(0.05)
        stop.set()
        return await asyncio.wait_for(task, timeout=2)  # not the 30 s poll

    assert asyncio.run(scenario()) == 0


def test_once_drains_the_queue(settings: Settings, sessions: sessionmaker[Session]) -> None:
    enqueue(sessions, 2)
    processed = asyncio.run(
        worker_main.serve(
            FinishingPipeline(sessions),  # type: ignore[arg-type]
            sessions,
            settings,
            once=True,
        )
    )
    assert processed == 2
    assert _states(sessions) == ["done", "done"]


# ---------------------------------------------------------------- warm-up


class EnvironmentOnlySandbox:
    async def environment(self) -> Any:
        from codeadapt.execution.models import EnvironmentInfo

        return EnvironmentInfo(
            backend="fake",
            image="img",
            image_id="sha256:0",
            compiler_version="g++ 0",
            container_runtime="runc",
            engine_version="0",
            host_kernel="0",
        )


def test_warm_up_measures_every_catalogue_version_once(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    catalogue = Catalogue.load(DEMO_CONTENT)
    with sessions() as s:
        catalogue.sync(s)
    pipeline = Pipeline(
        EnvironmentOnlySandbox(),  # type: ignore[arg-type]
        sessions,
        catalogue,
        FingerprintConsistencyV1(),
    )
    seen: list[tuple[str, int]] = []
    broken = catalogue.problems[0].version

    async def measured(_session: Session, problem: Any, environment: Any) -> Any:
        seen.append((problem.version, environment.id))
        if problem.version == broken:
            raise ContentUnavailableError("failed validation")
        return None

    monkeypatch.setattr(pipeline, "_fingerprints", measured)
    results = asyncio.run(pipeline.warm_up())
    assert [v for v, _ in seen] == [p.version for p in catalogue.problems]
    assert len({env for _, env in seen}) == 1  # one environment, as a submission would use
    assert len(results) == len(catalogue.problems)
    assert [k for k, ok in results.items() if not ok] == [
        f"{catalogue.problems[0].spec.slug}@{broken[:12]}"
    ]


# ---------------------------------------------------------------- D6 adaptation failure


class ExplodingPolicy(PolicyV1):
    def recommend(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("policy failed; dsn postgresql://u:pw-secret@db/x")


def _diagnosed(sessions: sessionmaker[Session]) -> tuple[int, Pipeline, Pipeline]:
    (job_id,) = enqueue(sessions)
    method = FingerprintConsistencyV1()
    record_diagnosis(sessions, job_id, method)
    with sessions() as s:
        s.execute(update(DiagnosisRow).values(outcome="no_failure_observed"))
        s.commit()
    catalogue = Catalogue.load(DEMO_CONTENT)
    failing = Pipeline(NoSandbox(), sessions, catalogue, method, ExplodingPolicy())
    working = Pipeline(NoSandbox(), sessions, catalogue, method, PolicyV1())
    return job_id, failing, working


def _adapt(sessions: sessionmaker[Session], pipeline: Pipeline, job_id: int) -> str | None:
    with sessions() as s:
        sub = s.get_one(Submission, s.get_one(Job, job_id).submission_id)
        row = s.scalars(select(DiagnosisRow).where(DiagnosisRow.submission_id == sub.id)).one()
        return pipeline.adapt_after_diagnosis(s, sub, row)


def _count(sessions: sessionmaker[Session], table: Any) -> int:
    with sessions() as s:
        return s.scalar(select(func.count()).select_from(table)) or 0


def test_adaptation_failure_keeps_the_diagnosis_and_is_reported(
    sessions: sessionmaker[Session],
) -> None:
    job_id, failing, _ = _diagnosed(sessions)
    error = _adapt(sessions, failing, job_id)
    assert error is not None and error.startswith("RuntimeError: policy failed")
    assert "pw-secret" not in error
    assert _count(sessions, DiagnosisRow) == 1  # the diagnosis survives
    assert _count(sessions, RecommendationRow) == 0  # no partial recommendation


def test_working_policy_path_is_unchanged(sessions: sessionmaker[Session]) -> None:
    job_id, _, working = _diagnosed(sessions)
    assert _adapt(sessions, working, job_id) is None
    assert _count(sessions, RecommendationRow) == 1


def test_handle_records_the_adaptation_marker_on_a_done_job(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    job_id, failing, _ = _diagnosed(sessions)
    with sessions() as s:  # a fresh submission run: no diagnosis yet from this method
        s.execute(update(DiagnosisRow).values(method_version="earlier"))
        s.commit()

    async def process(session: Session, submission_id: str) -> Any:
        sub = session.get_one(Submission, submission_id)
        row = session.scalars(
            select(DiagnosisRow).where(DiagnosisRow.submission_id == submission_id)
        ).one()
        error = failing.adapt_after_diagnosis(session, sub, row)
        assert error is not None
        failing.adaptation_errors[submission_id] = error
        return row

    monkeypatch.setattr(failing, "process", process)
    job = claim(sessions)
    assert job is not None
    asyncio.run(failing.handle(job))
    with sessions() as s:
        row = s.get_one(Job, job_id)
    assert row.state == JobState.DONE.value  # the student's diagnosis is delivered
    assert (row.last_error or "").startswith(ADAPTATION_FAILED + "RuntimeError")
    assert failing.adaptation_errors == {}


# ---------------------------------------------------------------- ops status


def test_status_is_ok_on_an_idle_database(sessions: sessionmaker[Session]) -> None:
    with sessions() as s:
        report = ops.collect(s, utcnow())
    assert report.queued == 0 and report.oldest_queued_seconds is None
    assert report.schema_revision == report.expected_schema_revision
    assert report.problems(ops.Thresholds()) == []


def test_status_flags_waiting_failed_and_adaptation_failed_jobs(
    sessions: sessionmaker[Session],
) -> None:
    ids = enqueue(sessions, 4)
    now = utcnow()
    with sessions() as s:
        s.execute(update(Job).where(Job.id == ids[0]).values(created_at=now - timedelta(hours=1)))
        s.execute(update(Job).where(Job.id == ids[1]).values(state=JobState.FAILED.value))
        s.execute(
            update(Job)
            .where(Job.id == ids[2])
            .values(state=JobState.DONE.value, last_error=ADAPTATION_FAILED + "RuntimeError: x")
        )
        s.execute(
            update(Job)
            .where(Job.id == ids[3])
            .values(state=JobState.RUNNING.value, lease_until=now - timedelta(minutes=1))
        )
        s.commit()
        report = ops.collect(s, now)
    assert (report.queued, report.running, report.running_with_expired_lease) == (1, 1, 1)
    assert report.failed_in_window == 1
    assert report.adaptation_failures_in_window == 1
    assert report.done_in_window == 1
    assert report.oldest_queued_seconds is not None and report.oldest_queued_seconds >= 3600
    problems = report.problems(ops.Thresholds())
    assert len(problems) == 4
    # Raised thresholds silence everything except the lost worker.
    lenient = ops.Thresholds(
        max_queue_age_seconds=7200, max_failed_jobs=5, max_adaptation_failures=5
    )
    assert report.problems(lenient) == ["1 running job(s) lost their worker"]


def test_status_command_prints_counts_only_and_signals_problems(
    db_url: str,
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("CODEADAPT_ENV", "test")
    monkeypatch.setenv("CODEADAPT_DATABASE_URL", db_url)
    assert admin.main(["status"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    enqueue(sessions)
    with sessions() as s:
        s.execute(update(Job).values(state=JobState.FAILED.value, last_error="secret detail"))
        s.commit()
    assert admin.main(["status"]) == 1
    out = capsys.readouterr().out
    assert json.loads(out)["failed_in_window"] == 1
    assert "secret detail" not in out
    assert admin.main(["status", "--max-failed-jobs", "1"]) == 0
