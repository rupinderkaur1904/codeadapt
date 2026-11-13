"""Gated self-service sign-up with invite codes (ADR-044)."""

from __future__ import annotations

import io
from dataclasses import replace
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from codeadapt import auth
from codeadapt.api.app import CSRF_HEADER, SESSION_COOKIE, create_app
from codeadapt.auth.cli import main as admin
from codeadapt.config import ConfigError, Environment, Settings, SignupMode
from codeadapt.db.models import AuditEvent, InviteCode, User, utcnow

PASSWORD = "correct horse battery"  # noqa: S105 - test fixture
BASE = "https://testserver"


def _settings(
    settings: Settings, mode: SignupMode = SignupMode.INVITE_CODE, **kw: object
) -> Settings:
    return replace(
        settings,
        env=Environment.PRODUCTION,
        allowed_hosts=("testserver",),
        signup_mode=mode,
        **kw,  # type: ignore[arg-type]
    )


@pytest.fixture
def client(settings: Settings, sessions: sessionmaker[Session]) -> TestClient:
    return TestClient(create_app(_settings(settings), sessions), base_url=BASE)


def _invite(
    sessions: sessionmaker[Session], max_uses: int = 5, valid_for: timedelta = timedelta(days=1)
) -> str:
    with sessions() as s:
        code, _ = auth.create_invite(s, "class A", max_uses, valid_for)
        s.commit()
    return code


def _signup(client: TestClient, username: str, code: str, password: str = PASSWORD) -> Any:
    return client.post(
        "/api/v1/auth/signup",
        json={"username": username, "password": password, "invite_code": code},
    )


def _kinds(sessions: sessionmaker[Session]) -> list[str]:
    with sessions() as s:
        return [e.kind for e in s.scalars(select(AuditEvent).order_by(AuditEvent.id))]


def test_signup_is_off_unless_configured(
    settings: Settings, sessions: sessionmaker[Session]
) -> None:
    off = TestClient(create_app(_settings(settings, SignupMode.OFF), sessions), base_url=BASE)
    assert off.get("/api/v1/auth/signup").json()["enabled"] is False
    code = _invite(sessions)
    r = _signup(off, "newbie", code)
    assert r.status_code == 403 and r.json()["type"].endswith("signup-disabled")
    with sessions() as s:
        assert s.scalar(select(User).where(User.username == "newbie")) is None
    assert (
        Settings(
            env=Environment.PRODUCTION, database_url="x", content_dir=settings.content_dir
        ).signup_enabled
        is False
    )


def test_signup_mode_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEADAPT_ENV", "test")
    monkeypatch.delenv("CODEADAPT_SIGNUP", raising=False)
    assert Settings.from_env().signup_mode is SignupMode.OFF
    monkeypatch.setenv("CODEADAPT_SIGNUP", "invite-code")
    assert Settings.from_env().signup_enabled
    monkeypatch.setenv("CODEADAPT_SIGNUP", "open")
    assert Settings.from_env().signup_enabled
    assert not Settings.from_env().signup_needs_invite_code
    for bad in ("on", "true", "Invite-Code", "OPEN"):
        monkeypatch.setenv("CODEADAPT_SIGNUP", bad)
        with pytest.raises(ConfigError, match="CODEADAPT_SIGNUP"):
            Settings.from_env()


def test_signup_creates_a_dev_student_and_logs_in(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    status = client.get("/api/v1/auth/signup").json()
    assert status == {"enabled": True, "needs_invite_code": True, "min_password_length": 12}
    code = _invite(sessions)
    # Codes are accepted however they are typed: lower case, spaces, without dashes.
    r = _signup(client, "Newbie", code.lower().replace("-", " "))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["username"] == "Newbie" and body["role"] == "student" and body["csrf_token"]
    assert "httponly" in r.headers["set-cookie"].lower()
    me = client.get("/api/v1/auth/me").json()
    assert me["username"] == "Newbie" and me["role"] == "student"
    with sessions() as s:
        user = s.scalars(select(User).where(User.username == "Newbie")).one()
        assert (user.role, user.data_class) == ("student", "dev")
        assert user.password_hash and user.password_hash.startswith("$argon2id$")
        assert s.scalars(select(InviteCode)).one().uses == 1
    # The new account logs in normally afterwards.
    fresh = TestClient(client.app, base_url=BASE)
    r = fresh.post("/api/v1/auth/login", json={"username": "newbie", "password": PASSWORD})
    assert r.status_code == 200
    assert "signup" in _kinds(sessions)


def test_caller_cannot_choose_role_or_data_class(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    code = _invite(sessions)
    for extra in ({"role": "researcher"}, {"data_class": "real"}):
        r = client.post(
            "/api/v1/auth/signup",
            json={"username": "sneaky", "password": PASSWORD, "invite_code": code, **extra},
        )
        assert r.status_code == 422
    with sessions() as s:
        assert s.scalar(select(User).where(User.username == "sneaky")) is None


@pytest.mark.parametrize("state", ["wrong", "expired", "revoked", "used-up"])
def test_unusable_codes_are_refused_alike(
    state: str, client: TestClient, sessions: sessionmaker[Session]
) -> None:
    code = _invite(sessions, max_uses=1)
    with sessions() as s:
        row = s.scalars(select(InviteCode)).one()
        if state == "expired":
            row.expires_at = utcnow() - timedelta(seconds=1)
        elif state == "revoked":
            row.revoked_at = utcnow()
        elif state == "used-up":
            row.uses = 1
        s.commit()
    r = _signup(client, "newbie", "WRONG-CODE-0000" if state == "wrong" else code)
    assert r.status_code == 403
    assert r.json()["type"].endswith("bad-invite-code")
    with sessions() as s:
        assert s.scalar(select(User).where(User.username == "newbie")) is None


def test_a_code_admits_at_most_max_uses_accounts(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    code = _invite(sessions, max_uses=2)
    assert _signup(TestClient(client.app, base_url=BASE), "one", code).status_code == 201
    assert _signup(TestClient(client.app, base_url=BASE), "two", code).status_code == 201
    assert _signup(TestClient(client.app, base_url=BASE), "three", code).status_code == 403


def test_password_and_username_rules(client: TestClient, sessions: sessionmaker[Session]) -> None:
    code = _invite(sessions, max_uses=1)
    assert _signup(client, "newbie", code, password="short").status_code == 422  # noqa: S106
    for name in ("ab", "dev-student", "DEV-admin", "admin", "Root", "has space", ".dot", "x" * 33):
        r = _signup(client, name, code)
        assert r.status_code == 422, name
    # None of the refusals spent the code's only use.
    assert _signup(client, "newbie", code).status_code == 201


def test_a_taken_name_ignoring_case_is_refused_and_keeps_the_use(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    with sessions() as s:
        s.add(User(username="Ana", role="student", data_class="synthetic"))
        s.commit()
    code = _invite(sessions, max_uses=1)
    r = _signup(client, "ana", code)
    assert r.status_code == 409
    with sessions() as s:
        assert s.scalars(select(InviteCode)).one().uses == 0
    assert _signup(client, "ana2", code).status_code == 201


def test_failed_signups_are_throttled_per_client(
    settings: Settings, sessions: sessionmaker[Session]
) -> None:
    c = TestClient(create_app(_settings(settings, signup_max_failures=3), sessions), base_url=BASE)
    code = _invite(sessions)
    for _ in range(3):
        assert _signup(c, "newbie", "WRONG-WRONG-WRON").status_code == 403
    # Now even the right code is refused from this client until the window passes.
    assert _signup(c, "newbie", code).status_code == 429
    assert "signup_throttled" in _kinds(sessions)


def test_successful_signups_are_capped_per_client(
    settings: Settings, sessions: sessionmaker[Session]
) -> None:
    app = create_app(_settings(settings, signups_per_client_per_hour=2), sessions)
    code = _invite(sessions)
    assert _signup(TestClient(app, base_url=BASE), "one", code).status_code == 201
    assert _signup(TestClient(app, base_url=BASE), "two", code).status_code == 201
    assert _signup(TestClient(app, base_url=BASE), "three", code).status_code == 429


def test_signup_rotates_an_existing_session(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    with sessions() as s:
        s.add(
            User(
                username="old",
                role="researcher",
                data_class="synthetic",
                password_hash=auth.hash_password(PASSWORD),
            )
        )
        s.commit()
    r = client.post("/api/v1/auth/login", json={"username": "old", "password": PASSWORD})
    old_token = client.cookies.get(SESSION_COOKIE)
    assert r.status_code == 200 and old_token
    assert _signup(client, "newbie", _invite(sessions)).status_code == 201
    assert client.get("/api/v1/auth/me").json()["username"] == "newbie"
    stale = TestClient(client.app, base_url=BASE, cookies={SESSION_COOKIE: old_token})
    assert stale.get("/api/v1/auth/me").status_code == 401
    # The new session needs its own CSRF token for writes, like any login.
    assert client.post("/api/v1/auth/logout").status_code == 403
    assert client.post("/api/v1/auth/logout", headers={CSRF_HEADER: "x"}).status_code == 403


def test_code_format_and_limits() -> None:
    assert auth.normalise_invite_code(" ab-cd ef ") == "ABCDEF"
    assert auth.format_invite_code("ABCDEFGHJKMN") == "ABCD-EFGH-JKMN"
    with pytest.raises(ValueError, match="max uses"):
        auth.create_invite(None, "x", 0, timedelta(days=1))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at most"):
        auth.create_invite(None, "x", 5, timedelta(days=91))  # type: ignore[arg-type]


def test_admin_cli_issues_lists_and_revokes_codes(
    db_url: str,
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("CODEADAPT_DATABASE_URL", db_url)
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert admin(["invite-create", "--label", "CS101 Tue", "--max-uses", "3", "--days", "7"]) == 0
    out = capsys.readouterr().out
    code = out.split(": ", 1)[1].split()[0]
    assert len(auth.normalise_invite_code(code)) == 12
    with sessions() as s:
        row = s.scalars(select(InviteCode)).one()
        assert row.code_hash != code and auth.normalise_invite_code(code) not in row.code_hash
        assert (row.label, row.max_uses, row.uses) == ("CS101 Tue", 3, 0)
        assert auth.consume_invite(s, code) is not None
        s.commit()
    assert admin(["invite-list"]) == 0
    assert "\tCS101 Tue\t1/3\t" in capsys.readouterr().out
    assert code not in capsys.readouterr().out
    assert admin(["invite-revoke", "1"]) == 0
    assert admin(["invite-list"]) == 0
    assert capsys.readouterr().out.rstrip().endswith("revoked")
    with sessions() as s:
        assert auth.consume_invite(s, code) is None
    with pytest.raises(SystemExit, match="at most"):
        admin(["invite-create", "--label", "x", "--days", "365"])
    assert {"invite_created", "invite_revoked"} <= set(_kinds(sessions))


# ---------------------------------------------------------------- open sign-up (ADR-046)


@pytest.fixture
def open_client(settings: Settings, sessions: sessionmaker[Session]) -> TestClient:
    return TestClient(create_app(_settings(settings, SignupMode.OPEN), sessions), base_url=BASE)


def _open_signup(client: TestClient, username: str, password: str = PASSWORD) -> Any:
    return client.post("/api/v1/auth/signup", json={"username": username, "password": password})


def test_open_signup_needs_no_invite_code(
    open_client: TestClient, sessions: sessionmaker[Session]
) -> None:
    status = open_client.get("/api/v1/auth/signup").json()
    assert status == {"enabled": True, "needs_invite_code": False, "min_password_length": 12}
    r = _open_signup(open_client, "Newbie")
    assert r.status_code == 201, r.text
    assert open_client.get("/api/v1/auth/me").json() == {
        "username": "Newbie",
        "role": "student",
        "csrf_token": r.json()["csrf_token"],
    }
    with sessions() as s:
        user = s.scalars(select(User).where(User.username == "Newbie")).one()
        assert (user.role, user.data_class) == ("student", "dev")
        event = s.scalars(select(AuditEvent).where(AuditEvent.kind == "signup")).one()
        assert event.target == "open"


def test_open_signup_keeps_every_other_rule(
    open_client: TestClient, sessions: sessionmaker[Session]
) -> None:
    for extra in ({"role": "admin"}, {"data_class": "real"}):
        body = {"username": "sneaky", "password": PASSWORD, **extra}
        assert open_client.post("/api/v1/auth/signup", json=body).status_code == 422
    assert _open_signup(open_client, "newbie", password="short").status_code == 422  # noqa: S106
    assert _open_signup(open_client, "dev-student").status_code == 422
    assert _open_signup(open_client, "admin").status_code == 422
    with sessions() as s:
        s.add(User(username="Ana", role="student", data_class="synthetic"))
        s.commit()
    assert _open_signup(open_client, "ana").status_code == 409
    with sessions() as s:
        assert s.scalar(select(User).where(User.username == "sneaky")) is None


def test_open_signup_failures_and_successes_are_limited_per_client(
    settings: Settings, sessions: sessionmaker[Session]
) -> None:
    app = create_app(
        _settings(settings, SignupMode.OPEN, signup_max_failures=2, signups_per_client_per_hour=2),
        sessions,
    )
    assert _open_signup(TestClient(app, base_url=BASE), "one").status_code == 201
    assert _open_signup(TestClient(app, base_url=BASE), "two").status_code == 201
    assert _open_signup(TestClient(app, base_url=BASE), "three").status_code == 429
    with sessions() as s:
        s.add(User(username="taken", role="student", data_class="synthetic"))
        s.commit()
    other = create_app(_settings(settings, SignupMode.OPEN, signup_max_failures=2), sessions)
    c = TestClient(other, base_url=BASE, client=("10.0.0.9", 1234))
    assert _open_signup(c, "taken").status_code == 409
    assert _open_signup(c, "taken").status_code == 409
    assert _open_signup(c, "fresh").status_code == 429


def test_daily_cap_counts_every_client(settings: Settings, sessions: sessionmaker[Session]) -> None:
    app = create_app(_settings(settings, SignupMode.OPEN, signups_per_day=2), sessions)
    for i, name in enumerate(("one", "two", "three")):
        c = TestClient(app, base_url=BASE, client=(f"10.0.0.{i + 1}", 1234))
        assert _open_signup(c, name).status_code == (201 if i < 2 else 429)


def test_invite_mode_still_requires_a_code(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    r = _open_signup(client, "newbie")
    assert r.status_code == 403 and r.json()["type"].endswith("bad-invite-code")
    with sessions() as s:
        assert s.scalar(select(User).where(User.username == "newbie")) is None
