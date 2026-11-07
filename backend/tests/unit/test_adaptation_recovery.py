"""D6 learner-facing behaviour (owner decision 2026-11-07, ADR-042).

After adaptation fails, the learner sees a neutral fallback instead of a recommendation or
follow-up verdict that predates their latest attempt; their work is kept; the error is
logged; and a retry runs the unchanged adaptation at most once.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, sessionmaker

from codeadapt import ops
from codeadapt.adaptation import PolicyV1
from codeadapt.api.app import create_app
from codeadapt.config import Settings
from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import (
    DiagnosisRow,
    FollowupEvaluationRow,
    Job,
    JobState,
    RecommendationRow,
    Submission,
    User,
    utcnow,
)
from codeadapt.diagnosis import FingerprintConsistencyV1
from codeadapt.worker.pipeline import Pipeline
from codeadapt.worker.recovery import (
    ADAPTATION_FAILED,
    ADAPTATION_RECOVERED,
    RetryResult,
    pending_failure,
    retry_adaptation,
)
from tests.conftest import POSTGRES_URL
from tests.paths import DEMO_CONTENT
from tests.unit.test_operations import ExplodingPolicy
from tests.unit.test_pipeline_redelivery import NoSandbox, record_diagnosis
from tests.unit.test_queue import enqueue


def _count(sessions: sessionmaker[Session], table: Any) -> int:
    with sessions() as s:
        return s.scalar(select(func.count()).select_from(table)) or 0


def _diagnose_both(sessions: sessionmaker[Session], ids: list[int]) -> None:
    """A recorded diagnosis for each job's submission, oldest submission first."""
    method = FingerprintConsistencyV1()
    record_diagnosis(sessions, ids[0], method)
    base = utcnow() - timedelta(minutes=10)
    with sessions() as s:
        first = s.scalars(select(DiagnosisRow)).one()
        for i, job_id in enumerate(ids):
            job = s.get_one(Job, job_id)
            s.execute(
                update(Submission)
                .where(Submission.id == job.submission_id)
                .values(created_at=base + timedelta(minutes=i))
            )
            if i > 0:
                s.add(
                    DiagnosisRow(
                        submission_id=job.submission_id,
                        run_id=first.run_id,
                        fingerprint_set_id=None,
                        method=first.method,
                        method_version=first.method_version,
                        outcome=first.outcome,
                        selected_model=first.selected_model,
                        candidates=list(first.candidates),
                        support=first.support,
                        rationale=first.rationale,
                    )
                )
        s.execute(update(DiagnosisRow).values(outcome="no_failure_observed"))
        s.commit()


def _adapt(sessions: sessionmaker[Session], pipeline: Pipeline, job_id: int) -> None:
    """Run the worker's adaptation step for one job, then finish the job as `handle` does."""
    with sessions() as s:
        job = s.get_one(Job, job_id)
        sub = s.get_one(Submission, job.submission_id)
        row = s.scalars(select(DiagnosisRow).where(DiagnosisRow.submission_id == sub.id)).one()
        error = pipeline.adapt_after_diagnosis(s, sub, row)
        s.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                state=JobState.DONE.value,
                last_error=f"{ADAPTATION_FAILED}{error}" if error is not None else None,
            )
        )
        s.commit()


@pytest.fixture
def failed_second_attempt(sessions: sessionmaker[Session]) -> tuple[list[int], int]:
    """Attempt 1 got a recommendation; adaptation then failed after attempt 2."""
    ids = enqueue(sessions, 2)
    _diagnose_both(sessions, ids)
    catalogue = Catalogue.load(DEMO_CONTENT)
    method = FingerprintConsistencyV1()
    working = Pipeline(NoSandbox(), sessions, catalogue, method, PolicyV1())
    failing = Pipeline(NoSandbox(), sessions, catalogue, method, ExplodingPolicy())
    _adapt(sessions, working, ids[0])
    _adapt(sessions, failing, ids[1])
    with sessions() as s:
        user_id = s.scalars(select(User.id)).one()
    assert _count(sessions, RecommendationRow) == 1
    return ids, user_id


def _retry(sessions: sessionmaker[Session], user_id: int, policy: PolicyV1) -> RetryResult:
    with sessions() as s:
        return retry_adaptation(s, user_id, Catalogue.load(DEMO_CONTENT), policy)


def _marker(sessions: sessionmaker[Session], job_id: int) -> str:
    with sessions() as s:
        return s.get_one(Job, job_id).last_error or ""


def test_failure_after_the_latest_attempt_is_pending(
    sessions: sessionmaker[Session], failed_second_attempt: tuple[list[int], int]
) -> None:
    ids, user_id = failed_second_attempt
    with sessions() as s:
        job = pending_failure(s, user_id)
    assert job is not None and job.id == ids[1]


def test_retry_recovers_exactly_once_and_keeps_previous_work(
    sessions: sessionmaker[Session], failed_second_attempt: tuple[list[int], int]
) -> None:
    ids, user_id = failed_second_attempt
    diagnoses = _count(sessions, DiagnosisRow)
    submissions = _count(sessions, Submission)

    assert _retry(sessions, user_id, PolicyV1()) is RetryResult.RECOVERED
    assert _count(sessions, RecommendationRow) == 2
    followups = _count(sessions, FollowupEvaluationRow)  # whatever the frozen policy decided
    assert _marker(sessions, ids[1]).startswith(ADAPTATION_RECOVERED + "RuntimeError")

    # Retrying again, as a double click or a reload would, changes nothing.
    for _ in range(3):
        assert _retry(sessions, user_id, PolicyV1()) is RetryResult.NOT_NEEDED
    assert _count(sessions, RecommendationRow) == 2
    assert _count(sessions, FollowupEvaluationRow) == followups
    # The learner's work and its diagnoses are never touched.
    assert (_count(sessions, DiagnosisRow), _count(sessions, Submission)) == (
        diagnoses,
        submissions,
    )
    with sessions() as s:
        assert pending_failure(s, user_id) is None
        newest = s.scalars(select(RecommendationRow).order_by(RecommendationRow.id.desc())).first()
        assert newest is not None
        assert newest.submission_id == s.get_one(Job, ids[1]).submission_id


def test_recovered_failure_still_counts_in_ops_status(
    sessions: sessionmaker[Session], failed_second_attempt: tuple[list[int], int]
) -> None:
    _, user_id = failed_second_attempt
    assert _retry(sessions, user_id, PolicyV1()) is RetryResult.RECOVERED
    with sessions() as s:
        report = ops.collect(s, utcnow())
    assert report.adaptation_failures_in_window == 1
    assert report.adaptation_recovered_in_window == 1


def test_failed_retry_keeps_the_fallback_and_logs_redacted(
    sessions: sessionmaker[Session],
    failed_second_attempt: tuple[list[int], int],
    caplog: pytest.LogCaptureFixture,
) -> None:
    ids, user_id = failed_second_attempt
    before = _marker(sessions, ids[1])
    with caplog.at_level(logging.ERROR, logger="codeadapt.worker.recovery"):
        assert _retry(sessions, user_id, ExplodingPolicy()) is RetryResult.FAILED
    assert _marker(sessions, ids[1]) == before  # still pending, still retryable
    assert _count(sessions, RecommendationRow) == 1
    assert _count(sessions, FollowupEvaluationRow) == 0
    logged = caplog.text
    assert "adaptation retry failed" in logged
    assert "pw-secret" not in logged
    # A later retry with a working policy still recovers it.
    assert _retry(sessions, user_id, PolicyV1()) is RetryResult.RECOVERED


def test_retry_is_refused_once_a_newer_attempt_exists(
    sessions: sessionmaker[Session], failed_second_attempt: tuple[list[int], int]
) -> None:
    ids, user_id = failed_second_attempt
    with sessions() as s:
        old = s.get_one(Submission, s.get_one(Job, ids[1]).submission_id)
        s.add(
            Submission(
                user_id=user_id,
                problem_version=old.problem_version,
                source="y",
                source_sha256="1" * 64,
                origin="student",
                data_class=old.data_class,
            )
        )
        s.commit()
    # The newer attempt's own adaptation will run with the full history; re-running the
    # old one now would see a history it never saw, so the retry does nothing.
    assert _retry(sessions, user_id, PolicyV1()) is RetryResult.SUPERSEDED
    assert _count(sessions, RecommendationRow) == 1
    assert _marker(sessions, ids[1]).startswith(ADAPTATION_FAILED)


def test_api_shows_the_fallback_then_recovers_on_retry(
    settings: Settings,
    sessions: sessionmaker[Session],
    failed_second_attempt: tuple[list[int], int],
) -> None:
    _, user_id = failed_second_attempt
    client = TestClient(create_app(settings, sessions))
    dev = {"X-Dev-Role": "student"}
    assert client.get("/api/v1/auth/me", headers=dev).status_code == 200
    with sessions() as s:  # hand the attempts to the dev student the client acts as
        dev_id = s.scalars(select(User.id).where(User.username == "dev-student")).one()
        s.execute(update(Submission).where(Submission.user_id == user_id).values(user_id=dev_id))
        s.execute(
            update(RecommendationRow)
            .where(RecommendationRow.user_id == user_id)
            .values(user_id=dev_id)
        )
        s.commit()

    body = client.get("/api/v1/me/recommendation", headers=dev).json()
    # The recommendation from attempt 1 exists but is withheld, and so is any verdict.
    assert body == {"recommendation": None, "last_followup": None, "adaptation_unavailable": True}

    retried = client.post("/api/v1/me/recommendation/retry", headers=dev)
    assert retried.status_code == 200
    body = retried.json()
    assert body["adaptation_unavailable"] is False
    assert body["recommendation"] is not None
    again = client.post("/api/v1/me/recommendation/retry", headers=dev).json()
    assert again == body
    assert _count(sessions, RecommendationRow) == 2


class SlowPolicy(PolicyV1):
    def recommend(self, *args: Any, **kwargs: Any) -> Any:
        time.sleep(0.5)  # hold the claimed row while a second retry arrives
        return super().recommend(*args, **kwargs)


@pytest.mark.skipif(not POSTGRES_URL, reason="row-lock race needs PostgreSQL")
def test_concurrent_retries_claim_the_failure_once(
    sessions: sessionmaker[Session], failed_second_attempt: tuple[list[int], int]
) -> None:
    _, user_id = failed_second_attempt
    results: list[RetryResult] = []
    start = threading.Barrier(2)

    def run() -> None:
        start.wait()
        results.append(_retry(sessions, user_id, SlowPolicy()))

    threads = [threading.Thread(target=run) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == [RetryResult.NOT_NEEDED, RetryResult.RECOVERED]
    assert _count(sessions, RecommendationRow) == 2
    assert _count(sessions, FollowupEvaluationRow) <= 1
