from datetime import timedelta

from sqlalchemy.orm import Session, sessionmaker

from codeadapt.content.catalogue import Catalogue
from codeadapt.db import queue
from codeadapt.db.models import DataClass, Job, JobState, Submission, User, utcnow
from tests.paths import DEMO_CONTENT


def enqueue(sessions: sessionmaker[Session], n: int = 1) -> list[int]:
    catalogue = Catalogue.load(DEMO_CONTENT)
    with sessions() as s:
        catalogue.sync(s)
        user = User(username="u", role="student", data_class=DataClass.DEV.value)
        s.add(user)
        s.flush()
        ids = []
        for _ in range(n):
            sub = Submission(
                user_id=user.id,
                problem_version=catalogue.problems[0].version,
                source="x",
                source_sha256="0" * 64,
                origin="student",
                data_class=DataClass.DEV.value,
            )
            s.add(sub)
            s.flush()
            job = Job(submission_id=sub.id)
            s.add(job)
            s.flush()
            ids.append(job.id)
        s.commit()
        return ids


def claim(sessions: sessionmaker[Session], worker: str = "w1", lease: float = 60) -> Job | None:
    with sessions() as s:
        return queue.claim_next(s, worker, lease_seconds=lease, max_attempts=3)


def test_claims_in_order_and_only_once(sessions: sessionmaker[Session]) -> None:
    ids = enqueue(sessions, 2)
    first, second = claim(sessions, "w1"), claim(sessions, "w2")
    assert first is not None and second is not None
    assert [first.id, second.id] == ids
    assert first.state == JobState.RUNNING.value and first.attempts == 1
    assert claim(sessions) is None


def test_stale_view_cannot_double_claim(sessions: sessionmaker[Session]) -> None:
    (job_id,) = enqueue(sessions)
    with sessions() as a, sessions() as b:
        stale = b.get_one(Job, job_id)  # b read the row while it was queued
        assert queue.claim_next(a, "a", lease_seconds=60, max_attempts=3) is not None
        # b's conditional update must not match any more.
        from sqlalchemy import update

        res = b.execute(
            update(Job)
            .where(Job.id == stale.id, Job.state == JobState.QUEUED.value, Job.attempts == 0)
            .values(state=JobState.RUNNING.value)
        )
        b.commit()
        assert res.rowcount == 0  # type: ignore[attr-defined]


def test_expired_lease_is_reclaimed_then_fails_after_max_attempts(
    sessions: sessionmaker[Session],
) -> None:
    (job_id,) = enqueue(sessions)
    for attempt in (1, 2, 3):
        job = claim(sessions, lease=-1)  # lease already expired
        assert job is not None and job.attempts == attempt
    assert claim(sessions) is None
    with sessions() as s:
        assert s.get_one(Job, job_id).state == JobState.FAILED.value


def test_finish_and_requeue(sessions: sessionmaker[Session]) -> None:
    enqueue(sessions)
    job = claim(sessions)
    assert job is not None
    with sessions() as s:
        queue.requeue(s, job, "sandbox down")
    again = claim(sessions)
    assert again is not None and again.attempts == 2
    with sessions() as s:
        queue.finish(s, again, state=JobState.DONE)
        row = s.get_one(Job, again.id)
        assert row.state == JobState.DONE.value
        assert row.lease_until is None
    assert claim(sessions) is None


def test_live_lease_is_not_reclaimed(sessions: sessionmaker[Session]) -> None:
    enqueue(sessions)
    assert claim(sessions, lease=timedelta(hours=1).total_seconds()) is not None
    assert claim(sessions) is None
    assert utcnow().tzinfo is not None
