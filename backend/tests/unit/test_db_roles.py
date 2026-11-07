"""ADR-042: the worker's PostgreSQL role can run the job pipeline but cannot read accounts,
sessions or the audit log. PostgreSQL only (CODEADAPT_TEST_POSTGRES_URL)."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterator
from dataclasses import replace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event, make_url, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session, sessionmaker

from codeadapt import auth, ops
from codeadapt.adaptation import PolicyV1
from codeadapt.api.app import CSRF_HEADER, create_app
from codeadapt.auth import cli as admin
from codeadapt.config import Environment, Settings
from codeadapt.content.catalogue import Catalogue
from codeadapt.db import roles
from codeadapt.db.models import (
    AuditEvent,
    DiagnosisRow,
    Job,
    JobState,
    RecommendationRow,
    Submission,
    User,
)
from codeadapt.db.session import make_engine, make_session_factory
from codeadapt.diagnosis import FingerprintConsistencyV1
from codeadapt.worker.pipeline import Pipeline
from tests.conftest import POSTGRES_URL
from tests.paths import DEMO_CONTENT
from tests.unit.test_pipeline_redelivery import NoSandbox, record_diagnosis
from tests.unit.test_queue import claim, enqueue

pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="needs CODEADAPT_TEST_POSTGRES_URL")


def test_statements_reject_unsafe_role_names() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        roles.grant_statements('api"; DROP TABLE users; --', "w")


@pytest.fixture
def role_names(db_url: str) -> Iterator[tuple[str, str]]:
    suffix = uuid.uuid4().hex[:8]
    api, worker = f"ca_api_{suffix}", f"ca_worker_{suffix}"
    owner = make_engine(db_url)
    with owner.begin() as conn:
        conn.execute(text(f'CREATE ROLE "{api}" NOLOGIN'))
        conn.execute(text(f'CREATE ROLE "{worker}" NOLOGIN'))
        for statement in roles.grant_statements(api, worker):
            conn.execute(text(statement))
    yield api, worker
    with owner.begin() as conn:
        for role in (api, worker):
            conn.execute(text(f'DROP OWNED BY "{role}"'))
            conn.execute(text(f'DROP ROLE "{role}"'))
    owner.dispose()


def _as_role(db_url: str, role: str) -> Engine:
    engine = make_engine(db_url)

    @event.listens_for(engine, "connect")
    def _set_role(dbapi_connection: Any, _record: Any) -> None:
        with dbapi_connection.cursor() as cursor:
            cursor.execute(f'SET ROLE "{role}"')
        dbapi_connection.commit()  # a rolled-back transaction would undo SET ROLE

    with engine.connect() as conn:  # guard: the tests below really run as `role`
        assert conn.execute(text("SELECT current_user")).scalar() == role
    return engine


def test_worker_role_cannot_read_accounts_sessions_or_audit(
    db_url: str, role_names: tuple[str, str]
) -> None:
    _, worker = role_names
    engine = _as_role(db_url, worker)
    for table in roles.WORKER_DENIED:
        with engine.connect() as conn, pytest.raises(ProgrammingError, match="permission denied"):
            conn.execute(text(f"SELECT * FROM {table} LIMIT 1"))  # noqa: S608 - fixed names
    with engine.connect() as conn, pytest.raises(ProgrammingError, match="permission denied"):
        conn.execute(text("CREATE TABLE intruder (x int)"))
    engine.dispose()


def test_worker_role_can_run_the_job_pipeline(
    db_url: str, sessions: sessionmaker[Session], role_names: tuple[str, str]
) -> None:
    _, worker = role_names
    (job_id,) = enqueue(sessions)  # the API creates users, submissions and jobs
    engine = _as_role(db_url, worker)
    as_worker = make_session_factory(engine)
    catalogue = Catalogue.load(DEMO_CONTENT)
    with as_worker() as s:
        catalogue.sync(s)  # start-up sync
    job = claim(as_worker)
    assert job is not None
    method = FingerprintConsistencyV1()
    record_diagnosis(as_worker, job_id, method)  # environment, run, diagnosis rows
    with sessions() as s:  # test setup, as the owner: the worker never updates diagnoses
        s.execute(text("UPDATE diagnoses SET outcome = 'no_failure_observed'"))
        s.commit()
    pipeline = Pipeline(NoSandbox(), as_worker, catalogue, method, PolicyV1())
    asyncio.run(pipeline.handle(job))  # redelivery path: finish without running
    with as_worker() as s:
        sub_id = s.get_one(Job, job_id).submission_id
        row = s.query(DiagnosisRow).filter_by(submission_id=sub_id).one()
        sub = s.get_one(Submission, sub_id)
        assert pipeline.adapt_after_diagnosis(s, sub, row) is None  # policy reads + writes
    with sessions() as s:
        assert s.get_one(Job, job_id).state == JobState.DONE.value
        assert s.query(RecommendationRow).count() == 1
    engine.dispose()


def test_api_role_has_data_access_but_no_ddl(db_url: str, role_names: tuple[str, str]) -> None:
    api, _ = role_names
    engine = _as_role(db_url, api)
    with engine.connect() as conn:
        conn.execute(text("SELECT count(*) FROM users"))
        conn.execute(text("SELECT count(*) FROM auth_sessions"))
        with pytest.raises(ProgrammingError, match="permission denied"):
            conn.execute(text("CREATE TABLE intruder (x int)"))
    engine.dispose()


def test_api_role_can_append_to_the_audit_log_but_never_rewrite_it(
    db_url: str, role_names: tuple[str, str]
) -> None:
    """R7 (owner, Gate B): a compromised API process cannot erase the access log."""
    api, _ = role_names
    engine = _as_role(db_url, api)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO audit_events (at, kind, username, client, target) "
                "VALUES (now(), 'login_failed', 'x', 'c', '')"
            )
        )
        assert conn.execute(text("SELECT count(*) FROM audit_events")).scalar() == 1
    for statement in (
        "UPDATE audit_events SET target = 'forged'",
        "DELETE FROM audit_events",
        "TRUNCATE audit_events",
    ):
        with engine.connect() as conn, pytest.raises(ProgrammingError, match="permission denied"):
            conn.execute(text(statement))
    engine.dispose()


def test_api_role_can_read_but_never_write_the_schema_revision(
    db_url: str, role_names: tuple[str, str]
) -> None:
    api, _ = role_names
    engine = _as_role(db_url, api)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    for statement in (
        "UPDATE alembic_version SET version_num = 'forged'",
        "DELETE FROM alembic_version",
        "INSERT INTO alembic_version (version_num) VALUES ('forged')",
        "TRUNCATE alembic_version",
    ):
        with engine.connect() as conn, pytest.raises(ProgrammingError, match="permission denied"):
            conn.execute(text(statement))
    engine.dispose()


def test_the_api_still_works_under_the_reduced_api_role(
    db_url: str, settings: Settings, role_names: tuple[str, str]
) -> None:
    """Login (audit + session rows), a failed login, logout and readiness, all as the API
    role: R7 removes nothing the application itself needs."""
    api, _ = role_names
    password = "correct horse battery"  # noqa: S105 - test fixture
    owner = make_session_factory(make_engine(db_url))
    with owner() as s:
        s.add(
            User(
                username="p001",
                role="student",
                data_class="synthetic",
                password_hash=auth.hash_password(password),
            )
        )
        s.commit()
    engine = _as_role(db_url, api)
    production = replace(settings, env=Environment.PRODUCTION, allowed_hosts=("testserver",))
    client = TestClient(
        create_app(production, make_session_factory(engine)), base_url="https://testserver"
    )
    bad = client.post("/api/v1/auth/login", json={"username": "p001", "password": "wrong"})
    assert bad.status_code == 401
    ok = client.post("/api/v1/auth/login", json={"username": "p001", "password": password})
    assert ok.status_code == 200, ok.text
    assert client.get("/api/v1/me/recommendation").status_code == 200
    out = client.post("/api/v1/auth/logout", headers={CSRF_HEADER: ok.json()["csrf_token"]})
    assert out.status_code == 204
    assert client.get("/api/v1/ready").json() == {"status": "ready"}
    with owner() as s:
        assert s.query(AuditEvent).count() >= 2  # the failed and the successful login
    engine.dispose()


def test_erasure_needs_the_owner_connection_and_works_through_it(
    db_url: str,
    role_names: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """R7: erase-learner deletes and scrubs audit rows, so the API role can no longer run
    it; the owner connection (the `admin` Compose service) can, and so can purge-sessions."""
    api, _ = role_names
    owner = make_session_factory(make_engine(db_url))
    with owner() as s:
        user = User(username="p017", role="student", data_class="synthetic")
        s.add(user)
        s.flush()
        auth.audit(s, "login", username="p017", client="c", user=user)
        s.commit()
        user_id = user.id
    as_api = make_session_factory(_as_role(db_url, api))
    with as_api() as s, pytest.raises(ProgrammingError, match="permission denied"):
        ops.erase_learner(s, user_id, apply=True)
    monkeypatch.setenv("CODEADAPT_ENV", "test")
    url = make_url(db_url)
    with owner() as s:  # a login role with the API's grants, to run the CLI as the API
        s.execute(text(f'CREATE ROLE "{api}_login" LOGIN PASSWORD \'pw-{api}\' IN ROLE "{api}"'))
        s.commit()
    try:
        api_url = url.set(username=f"{api}_login", password=f"pw-{api}")
        monkeypatch.setenv("CODEADAPT_DATABASE_URL", api_url.render_as_string(hide_password=False))
        with pytest.raises(SystemExit, match="schema owner"):
            admin.main(["erase-learner", "p017", "--apply"])
    finally:
        with owner() as s:
            s.execute(text(f'DROP ROLE "{api}_login"'))
            s.commit()

    monkeypatch.setenv("CODEADAPT_DATABASE_URL", db_url)  # the owner connection
    assert admin.main(["erase-learner", "p017", "--apply"]) == 0
    assert admin.main(["purge-sessions", "--apply"]) == 0
    capsys.readouterr()
    with owner() as s:
        assert s.get(User, user_id) is None
        assert s.query(AuditEvent).filter_by(username="p017").count() == 0


def test_db_setup_creates_login_roles_that_can_connect(
    db_url: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    suffix = uuid.uuid4().hex[:8]
    api, worker = f"ca_api_{suffix}", f"ca_worker_{suffix}"
    api_pw, worker_pw = "api-" + uuid.uuid4().hex, "worker-" + uuid.uuid4().hex
    monkeypatch.setenv("CODEADAPT_ENV", "test")
    monkeypatch.setenv("CODEADAPT_DATABASE_URL", db_url)
    monkeypatch.setenv("CODEADAPT_API_DB_PASSWORD", api_pw)
    monkeypatch.setenv("CODEADAPT_WORKER_DB_PASSWORD", worker_pw)
    try:
        assert admin.main(["db-setup", "--api-role", api, "--worker-role", worker]) == 0
        assert admin.main(["db-setup", "--api-role", api, "--worker-role", worker]) == 0
        out = capsys.readouterr().out
        assert api_pw not in out and worker_pw not in out
        url = make_url(db_url)
        as_worker = make_engine(
            url.set(username=worker, password=worker_pw).render_as_string(hide_password=False)
        )
        with as_worker.connect() as conn:
            assert conn.execute(text("SELECT current_user")).scalar() == worker
            conn.execute(text("SELECT count(*) FROM jobs"))
            with pytest.raises(ProgrammingError, match="permission denied"):
                conn.execute(text("SELECT count(*) FROM users"))
        as_worker.dispose()
    finally:
        owner = make_engine(db_url)
        with owner.begin() as conn:
            for role in (api, worker):
                conn.execute(text(f'DROP OWNED BY "{role}"'))
                conn.execute(text(f'DROP ROLE IF EXISTS "{role}"'))
        owner.dispose()


def test_db_setup_refuses_placeholder_passwords(
    db_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CODEADAPT_ENV", "test")
    monkeypatch.setenv("CODEADAPT_DATABASE_URL", db_url)
    monkeypatch.setenv("CODEADAPT_API_DB_PASSWORD", "CHANGE_ME_api_password")
    monkeypatch.setenv("CODEADAPT_WORKER_DB_PASSWORD", "x" * 32)
    with pytest.raises(SystemExit, match="CODEADAPT_API_DB_PASSWORD"):
        admin.main(["db-setup"])
