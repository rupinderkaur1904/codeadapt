"""Login sessions, CSRF, rate limits, audit log and the admin CLI (ADR-029)."""

import io
import sqlite3
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from codeadapt import auth
from codeadapt.api.app import CSRF_HEADER, SESSION_COOKIE, create_app
from codeadapt.auth.cli import main as admin
from codeadapt.config import Environment, Settings
from codeadapt.db.models import AuditEvent, AuthSession, User

PASSWORD = "correct horse battery"  # noqa: S105 - test fixture


@pytest.fixture
def production(settings: Settings) -> Settings:
    return replace(settings, env=Environment.PRODUCTION, submissions_per_minute=2)


@pytest.fixture
def client(production: Settings, sessions: sessionmaker[Session]) -> TestClient:
    # https base URL so the Secure cookie is sent back, as in production.
    return TestClient(create_app(production, sessions), base_url="https://testserver")


def _user(sessions: sessionmaker[Session], username: str, role: str = "student") -> None:
    with sessions() as s:
        s.add(
            User(
                username=username,
                role=role,
                data_class="synthetic",
                password_hash=auth.hash_password(PASSWORD),
            )
        )
        s.commit()


def _login(client: TestClient, username: str, password: str = PASSWORD) -> str:
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return str(r.json()["csrf_token"])


def _events(sessions: sessionmaker[Session], kind: str) -> list[AuditEvent]:
    with sessions() as s:
        return list(s.scalars(select(AuditEvent).where(AuditEvent.kind == kind)))


def test_passwords_are_argon2id_and_short_ones_are_refused() -> None:
    stored = auth.hash_password(PASSWORD)
    assert stored.startswith("$argon2id$")
    assert auth.verify_password(stored, PASSWORD)
    assert not auth.verify_password(stored, PASSWORD + "x")
    assert not auth.verify_password(None, PASSWORD)
    with pytest.raises(ValueError, match="at least"):
        auth.hash_password("short")


def test_login_sets_a_hardened_cookie_and_stores_only_a_token_digest(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    _user(sessions, "ana")
    r = client.post("/api/v1/auth/login", json={"username": "ana", "password": PASSWORD})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    for attribute in ("httponly", "secure", "samesite=strict", "path=/api"):
        assert attribute in cookie
    token = client.cookies[SESSION_COOKIE]
    with sessions() as s:
        rows = list(s.scalars(select(AuthSession)))
    assert len(rows) == 1
    assert token not in {rows[0].token_hash, rows[0].csrf_token}
    me = client.get("/api/v1/auth/me").json()
    assert me == {"username": "ana", "role": "student", "csrf_token": r.json()["csrf_token"]}
    assert len(_events(sessions, auth.AuditKind.LOGIN)) == 1


def test_wrong_password_unknown_user_and_disabled_account_all_fail_alike(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    _user(sessions, "ben")
    with sessions() as s:
        s.add(User(username="nopass", role="student", data_class="dev"))
        s.commit()
    for username, password in (("ben", "wrong password!"), ("ghost", PASSWORD), ("nopass", "")):
        r = client.post(
            "/api/v1/auth/login", json={"username": username, "password": password or "x"}
        )
        assert r.status_code == 401
        assert r.json()["type"].endswith("/login-failed")
    assert SESSION_COOKIE not in client.cookies


def test_state_changing_requests_need_the_csrf_token(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    _user(sessions, "cy")
    csrf = _login(client, "cy")
    body = {"problem_slug": "lower-bound", "source": "int x;"}
    missing = client.post("/api/v1/submissions", json=body)
    assert missing.status_code == 403
    assert missing.json()["type"].endswith("/csrf-failed")
    wrong = client.post("/api/v1/submissions", json=body, headers={CSRF_HEADER: "nope"})
    assert wrong.status_code == 403
    ok = client.post("/api/v1/submissions", json=body, headers={CSRF_HEADER: csrf})
    assert ok.status_code == 202
    assert client.get("/api/v1/problems").status_code == 200  # reads need no token


def test_logout_revokes_the_session(client: TestClient, sessions: sessionmaker[Session]) -> None:
    _user(sessions, "dee")
    csrf = _login(client, "dee")
    token = client.cookies[SESSION_COOKIE]
    assert client.post("/api/v1/auth/logout", headers={CSRF_HEADER: csrf}).status_code == 204
    client.cookies.set(SESSION_COOKIE, token, domain="testserver", path="/api")  # replay
    r = client.get("/api/v1/problems")
    assert r.status_code == 401
    assert r.json()["type"].endswith("/not-authenticated")


def test_expired_and_disabled_sessions_are_rejected(
    production: Settings, client: TestClient, sessions: sessionmaker[Session]
) -> None:
    _user(sessions, "eve")
    expired = TestClient(
        create_app(replace(production, session_hours=-1), sessions),
        base_url="https://testserver",
    )
    expired.post("/api/v1/auth/login", json={"username": "eve", "password": PASSWORD})
    assert expired.get("/api/v1/problems").status_code == 401
    _login(client, "eve")
    with sessions() as s:
        user = s.scalars(select(User).where(User.username == "eve")).one()
        user.disabled = True
        s.commit()
    assert client.get("/api/v1/problems").status_code == 401


def test_repeated_failed_logins_are_throttled(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    _user(sessions, "fay")
    for _ in range(5):
        r = client.post("/api/v1/auth/login", json={"username": "fay", "password": "bad guess!"})
        assert r.status_code == 401
    # Even the right password is refused inside the window.
    r = client.post("/api/v1/auth/login", json={"username": "fay", "password": PASSWORD})
    assert r.status_code == 429
    assert len(_events(sessions, auth.AuditKind.LOGIN_FAILED)) == 5
    assert len(_events(sessions, auth.AuditKind.LOGIN_THROTTLED)) == 1


def test_submissions_are_rate_limited_per_user(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    _user(sessions, "gus")
    csrf = _login(client, "gus")
    body = {"problem_slug": "lower-bound", "source": "int x;"}
    codes = [
        client.post("/api/v1/submissions", json=body, headers={CSRF_HEADER: csrf}).status_code
        for _ in range(3)
    ]
    assert codes == [202, 202, 429]


def test_researcher_access_is_audited(client: TestClient, sessions: sessionmaker[Session]) -> None:
    _user(sessions, "stu")
    _user(sessions, "res", role="researcher")
    student = TestClient(client.app, base_url="https://testserver")
    csrf = _login(student, "stu")
    sub_id = student.post(
        "/api/v1/submissions",
        json={"problem_slug": "lower-bound", "source": "int x;"},
        headers={CSRF_HEADER: csrf},
    ).json()["id"]
    assert student.get("/api/v1/research/metrics").status_code == 403
    _login(client, "res")
    assert client.get("/api/v1/research/metrics?data_class=real").status_code == 200
    assert client.get(f"/api/v1/submissions/{sub_id}").status_code == 200
    research = _events(sessions, auth.AuditKind.RESEARCH_ACCESS)
    assert [(e.username, e.target) for e in research] == [
        ("res", "/api/v1/research/metrics?data_class=real")
    ]
    views = _events(sessions, auth.AuditKind.STAFF_VIEW_SUBMISSION)
    assert [(e.username, e.target) for e in views] == [("res", sub_id)]
    # A student reading their own submission is not a staff view.
    student.get(f"/api/v1/submissions/{sub_id}")
    assert len(_events(sessions, auth.AuditKind.STAFF_VIEW_SUBMISSION)) == 1


def test_admin_cli_creates_resets_and_disables_accounts(
    db_url: str,
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("CODEADAPT_DATABASE_URL", db_url)
    monkeypatch.setattr("sys.stdin", io.StringIO(PASSWORD + "\n"))
    assert admin(["create-user", "hal", "--role", "researcher", "--data-class", "real"]) == 0
    with sessions() as s:
        hal = s.scalars(select(User).where(User.username == "hal")).one()
        assert hal.role == "researcher"
        assert auth.verify_password(hal.password_hash, PASSWORD)
        auth.start_session(s, hal, timedelta(hours=1))
        s.commit()
    assert admin(["disable", "hal"]) == 0
    with sessions() as s:
        hal = s.scalars(select(User).where(User.username == "hal")).one()
        assert hal.disabled
        assert all(r.revoked_at is not None for r in s.scalars(select(AuthSession)))
    monkeypatch.setattr("sys.stdin", io.StringIO("short\n"))
    with pytest.raises(ValueError, match="at least"):
        admin(["set-password", "hal"])
    admin(["list"])
    assert "hal\tresearcher\treal\tdisabled" in capsys.readouterr().out
    kinds = [e.kind for e in _events(sessions, auth.AuditKind.ACCOUNT_CREATED)]
    assert kinds == ["account_created"]


def test_admin_backup_copies_a_consistent_sqlite_database(
    db_url: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CODEADAPT_DATABASE_URL", db_url)
    destination = tmp_path / "backup.sqlite3"
    assert admin(["backup", str(destination)]) == 0
    copy = sqlite3.connect(destination)
    assert copy.execute("SELECT version_num FROM alembic_version").fetchone() == ("0005",)
    copy.close()
    with pytest.raises(SystemExit, match="refusing"):
        admin(["backup", str(destination)])
