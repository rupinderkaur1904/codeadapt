"""ADR-041: case-insensitive usernames (migration 0006), session rotation at login, and
self-service password change. Runs on SQLite and, with CODEADAPT_TEST_POSTGRES_URL, PostgreSQL."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from alembic import command
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, make_url, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from codeadapt import auth
from codeadapt.api.app import CSRF_HEADER, SESSION_COOKIE, create_app
from codeadapt.config import Environment, Settings
from codeadapt.db.migrate import alembic_config
from codeadapt.db.models import AuditEvent, AuthSession, User
from tests.conftest import POSTGRES_URL

PASSWORD = "correct horse battery"  # noqa: S105 - test fixture
NEW_PASSWORD = "a brand new passphrase"  # noqa: S105 - test fixture
BASE = "https://testserver"


@pytest.fixture
def production(settings: Settings) -> Settings:
    return replace(settings, env=Environment.PRODUCTION, allowed_hosts=("testserver",))


@pytest.fixture
def app(production: Settings, sessions: sessionmaker[Session]) -> FastAPI:
    return create_app(production, sessions)


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


# ---------------------------------------------------------------- usernames


def test_database_refuses_names_that_differ_only_in_case(sessions: sessionmaker[Session]) -> None:
    _user(sessions, "Alice")
    with pytest.raises(IntegrityError), sessions() as s:
        s.add(User(username="aLICE", role="student", data_class="synthetic"))
        s.commit()
    with sessions() as s:
        index = {i["name"]: i for i in inspect(s.get_bind()).get_indexes("users")}.get(
            "ux_users_username_lower"
        )
    # SQLite cannot reflect expression indexes (it reports the name only); PostgreSQL can.
    assert index is not None or not POSTGRES_URL


def test_login_and_lookup_ignore_case(app: FastAPI, sessions: sessionmaker[Session]) -> None:
    _user(sessions, "Alice")
    client = TestClient(app, base_url=BASE)
    _login(client, "aLiCe")
    assert client.get("/api/v1/auth/me").json()["username"] == "Alice"  # spelling kept
    with sessions() as s:
        assert auth.find_user(s, "ALICE") is not None


def test_throttle_is_not_reset_by_changing_case(
    app: FastAPI, sessions: sessionmaker[Session]
) -> None:
    _user(sessions, "bob")
    for i, name in enumerate(["bob", "BOB", "Bob", "bOb", "boB"]):
        client = TestClient(app, base_url=BASE, client=(f"10.0.0.{i}", 1234))
        r = client.post("/api/v1/auth/login", json={"username": name, "password": "wrong!"})
        assert r.status_code == 401
    client = TestClient(app, base_url=BASE, client=("10.0.0.99", 1234))
    r = client.post("/api/v1/auth/login", json={"username": "BoB", "password": PASSWORD})
    assert r.status_code == 429


# ---------------------------------------------------------------- migration 0006


@pytest.fixture
def blank_db_url(tmp_path: Path) -> Iterator[str]:
    """An empty database (not migrated), on the same engine as the rest of the suite."""
    if not POSTGRES_URL:
        yield f"sqlite:///{tmp_path / 'blank.sqlite3'}"
        return
    name = f"codeadapt_mig_{uuid.uuid4().hex[:12]}"
    admin = create_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    yield make_url(POSTGRES_URL).set(database=name).render_as_string(hide_password=False)
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
    admin.dispose()


def _insert_users(url: str, *names: str) -> None:
    engine = create_engine(url)
    with engine.begin() as conn:
        for n in names:
            conn.execute(
                text(
                    "INSERT INTO users (username, role, data_class, created_at, disabled) "
                    "VALUES (:n, 'student', 'synthetic', CURRENT_TIMESTAMP, false)"
                ),
                {"n": n},
            )
    engine.dispose()


def _usernames(url: str) -> list[str]:
    engine = create_engine(url)
    with engine.connect() as conn:
        names = [r[0] for r in conn.execute(text("SELECT username FROM users ORDER BY id"))]
    engine.dispose()
    return names


def test_upgrade_from_0005_keeps_rows_and_downgrade_drops_the_index(blank_db_url: str) -> None:
    cfg = alembic_config(blank_db_url)
    command.upgrade(cfg, "0005")
    _insert_users(blank_db_url, "Alice", "bob", "Carol")
    command.upgrade(cfg, "0006")
    assert _usernames(blank_db_url) == ["Alice", "bob", "Carol"]
    with pytest.raises(IntegrityError):
        _insert_users(blank_db_url, "ALICE")
    command.downgrade(cfg, "0005")
    _insert_users(blank_db_url, "ALICE")  # allowed again without the index
    assert _usernames(blank_db_url) == ["Alice", "bob", "Carol", "ALICE"]


def test_upgrade_stops_and_lists_existing_collisions(blank_db_url: str) -> None:
    cfg = alembic_config(blank_db_url)
    command.upgrade(cfg, "0005")
    _insert_users(blank_db_url, "Alice", "alice", "bob", "BOB", "carol")
    with pytest.raises(RuntimeError, match=r"'alice' \(2 accounts\), 'bob' \(2 accounts\)"):
        command.upgrade(cfg, "0006")
    assert _usernames(blank_db_url) == ["Alice", "alice", "bob", "BOB", "carol"]
    engine = create_engine(blank_db_url)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0005"
    engine.dispose()


# ---------------------------------------------------------------- session rotation


def test_login_ends_the_browsers_previous_session(
    app: FastAPI, sessions: sessionmaker[Session]
) -> None:
    _user(sessions, "dan")
    _user(sessions, "eve")
    client = TestClient(app, base_url=BASE)
    _login(client, "dan")
    first = client.cookies[SESSION_COOKIE]
    _login(client, "eve")  # another account in the same browser
    second = client.cookies[SESSION_COOKIE]
    assert first != second
    stale = TestClient(app, base_url=BASE, cookies={SESSION_COOKIE: first})
    assert stale.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me").json()["username"] == "eve"
    # A login on another device does not end this one.
    other = TestClient(app, base_url=BASE)
    _login(other, "eve")
    assert client.get("/api/v1/auth/me").status_code == 200


# ---------------------------------------------------------------- password change


def test_password_change_rotates_every_session(
    app: FastAPI, sessions: sessionmaker[Session]
) -> None:
    _user(sessions, "fay")
    laptop, phone = TestClient(app, base_url=BASE), TestClient(app, base_url=BASE)
    csrf = _login(laptop, "fay")
    _login(phone, "fay")
    old_cookie = laptop.cookies[SESSION_COOKIE]
    r = laptop.post(
        "/api/v1/auth/password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers={CSRF_HEADER: csrf},
    )
    assert r.status_code == 200, r.text
    new_csrf = r.json()["csrf_token"]
    assert new_csrf != csrf
    assert laptop.cookies[SESSION_COOKIE] != old_cookie
    assert laptop.get("/api/v1/auth/me").status_code == 200  # this browser carries on
    assert phone.get("/api/v1/auth/me").status_code == 401  # every other session ended
    stale = TestClient(app, base_url=BASE, cookies={SESSION_COOKIE: old_cookie})
    assert stale.get("/api/v1/auth/me").status_code == 401
    fresh = TestClient(app, base_url=BASE)
    r = fresh.post("/api/v1/auth/login", json={"username": "fay", "password": PASSWORD})
    assert r.status_code == 401
    _login(fresh, "fay", NEW_PASSWORD)
    with sessions() as s:
        live = s.scalars(select(AuthSession).where(AuthSession.revoked_at.is_(None))).all()
        assert len(live) == 2  # the laptop's new session and the fresh login
    assert len(_events(sessions, auth.AuditKind.PASSWORD_CHANGED)) == 1


def test_password_change_refusals(app: FastAPI, sessions: sessionmaker[Session]) -> None:
    _user(sessions, "gus")
    client = TestClient(app, base_url=BASE)
    csrf = _login(client, "gus")
    url = "/api/v1/auth/password"
    good = {"current_password": PASSWORD, "new_password": NEW_PASSWORD}
    anonymous = TestClient(app, base_url=BASE)
    assert anonymous.post(url, json=good).status_code == 401
    assert client.post(url, json=good).status_code == 403  # no CSRF token
    r = client.post(
        url,
        json={"current_password": "not it", "new_password": NEW_PASSWORD},
        headers={CSRF_HEADER: csrf},
    )
    assert r.status_code == 403
    assert r.json()["type"].endswith("/wrong-password")
    assert len(_events(sessions, auth.AuditKind.PASSWORD_CHANGE_FAILED)) == 1
    r = client.post(
        url,
        json={"current_password": PASSWORD, "new_password": "short"},
        headers={CSRF_HEADER: csrf},
    )
    assert r.status_code == 422
    assert r.json()["type"].endswith("/weak-password")
    # Nothing changed: the old password still works and the session is still live.
    assert client.get("/api/v1/auth/me").status_code == 200
    _login(TestClient(app, base_url=BASE), "gus")


def test_wrong_current_passwords_count_towards_the_throttle(
    app: FastAPI,
    sessions: sessionmaker[Session],
) -> None:
    _user(sessions, "hal")
    client = TestClient(app, base_url=BASE)
    csrf = _login(client, "hal")
    bad = {"current_password": "guess!", "new_password": NEW_PASSWORD}
    codes = [
        client.post("/api/v1/auth/password", json=bad, headers={CSRF_HEADER: csrf}).status_code
        for _ in range(6)
    ]
    assert codes == [403] * 5 + [429]


def test_dev_stub_cannot_change_a_password(
    settings: Settings, sessions: sessionmaker[Session]
) -> None:
    client = TestClient(create_app(settings, sessions))  # TEST env: X-Dev-Role stub
    r = client.post(
        "/api/v1/auth/password",
        json={"current_password": "x", "new_password": NEW_PASSWORD},
        headers={"X-Dev-Role": "student"},
    )
    assert r.status_code == 403
