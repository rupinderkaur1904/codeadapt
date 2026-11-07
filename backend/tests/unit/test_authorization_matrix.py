"""Authorization matrix and IDOR checks in production mode, with real login sessions (ADR-040).

Every principal is a real account with a password-login session, as in production: the
development X-Dev-Role stub is off. The table states the expected status for each endpoint and
principal; a new endpoint that takes no login at all fails `test_every_api_route_needs_login`.
"""

from __future__ import annotations

import re
from dataclasses import replace

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from codeadapt import auth
from codeadapt.api.app import CSRF_HEADER, create_app
from codeadapt.config import Environment, Settings
from codeadapt.db.models import User

PASSWORD = "correct horse battery"  # noqa: S105 - test fixture
BASE = "https://testserver"
PRINCIPALS = ("anonymous", "owner", "other_student", "researcher", "admin", "unknown_role")
ROLES = {
    "owner": "student",
    "other_student": "student",
    "researcher": "researcher",
    "admin": "admin",
    "unknown_role": "superuser",  # not a role the code knows: must be denied everything
}
# Routes that need no login by design. Anything else under /api must refuse anonymous callers.
PUBLIC = {("POST", "/api/v1/auth/login"), ("GET", "/api/v1/health")}


@pytest.fixture
def app_and_clients(
    settings: Settings, sessions: sessionmaker[Session]
) -> tuple[object, dict[str, TestClient], dict[str, str], str]:
    production = replace(settings, env=Environment.PRODUCTION, allowed_hosts=("testserver",))
    app = create_app(production, sessions)
    with sessions() as s:
        for name, role in ROLES.items():
            s.add(
                User(
                    username=name,
                    role=role,
                    data_class="synthetic",
                    password_hash=auth.hash_password(PASSWORD),
                )
            )
        s.commit()
    clients: dict[str, TestClient] = {"anonymous": TestClient(app, base_url=BASE)}
    csrf: dict[str, str] = {}
    for name in ROLES:
        c = TestClient(app, base_url=BASE)
        r = c.post("/api/v1/auth/login", json={"username": name, "password": PASSWORD})
        assert r.status_code == 200, r.text
        clients[name], csrf[name] = c, r.json()["csrf_token"]
    sub = clients["owner"].post(
        "/api/v1/submissions",
        json={"problem_slug": "lower-bound", "source": "int x;"},
        headers={CSRF_HEADER: csrf["owner"]},
    )
    assert sub.status_code == 202, sub.text
    return app, clients, csrf, sub.json()["id"]


# endpoint template -> expected status per principal, in PRINCIPALS order.
MATRIX: list[tuple[str, tuple[int, ...]]] = [
    # A student's own submission: owner and staff may read it; another student gets 404 so the
    # identifier's existence is not revealed.
    ("/api/v1/submissions/{sub}", (401, 200, 404, 200, 200, 403)),
    ("/api/v1/submissions/{missing}", (401, 404, 404, 404, 404, 403)),
    ("/api/v1/research/submissions/{sub}/trace", (401, 403, 403, 200, 200, 403)),
    ("/api/v1/research/learner-model?username=owner", (401, 403, 403, 200, 200, 403)),
    ("/api/v1/research/submissions", (401, 403, 403, 200, 200, 403)),
    ("/api/v1/research/metrics", (401, 403, 403, 200, 200, 403)),
    ("/api/v1/submissions", (401, 200, 200, 200, 200, 403)),
    ("/api/v1/me/recommendation", (401, 200, 200, 200, 200, 403)),
    ("/api/v1/problems", (401, 200, 200, 200, 200, 403)),
    ("/api/v1/auth/me", (401, 200, 200, 200, 200, 403)),
]


@pytest.mark.parametrize(("template", "expected"), MATRIX, ids=[m[0] for m in MATRIX])
def test_permission_matrix(
    app_and_clients: tuple[object, dict[str, TestClient], dict[str, str], str],
    template: str,
    expected: tuple[int, ...],
) -> None:
    _, clients, _, sub_id = app_and_clients
    url = template.format(sub=sub_id, missing="0" * 32)
    got = tuple(clients[p].get(url).status_code for p in PRINCIPALS)
    assert dict(zip(PRINCIPALS, got, strict=True)) == dict(zip(PRINCIPALS, expected, strict=True))


def test_lists_show_only_the_callers_own_submissions(
    app_and_clients: tuple[object, dict[str, TestClient], dict[str, str], str],
) -> None:
    _, clients, _, sub_id = app_and_clients
    own = [s["id"] for s in clients["owner"].get("/api/v1/submissions").json()]
    other = [s["id"] for s in clients["other_student"].get("/api/v1/submissions").json()]
    assert own == [sub_id]
    assert other == []
    # Staff reading their *own* list do not see students' submissions there either.
    assert clients["researcher"].get("/api/v1/submissions").json() == []


def test_dev_role_header_never_grants_anything_in_production(
    app_and_clients: tuple[object, dict[str, TestClient], dict[str, str], str],
) -> None:
    _, clients, _, sub_id = app_and_clients
    header = {"X-Dev-Role": "researcher"}
    # Without a session: still unauthenticated.
    assert clients["anonymous"].get("/api/v1/research/metrics", headers=header).status_code == 401
    # Next to a student's session: the header is ignored; the student stays a student.
    student = clients["other_student"]
    assert student.get("/api/v1/research/metrics", headers=header).status_code == 403
    assert student.get(f"/api/v1/submissions/{sub_id}", headers=header).status_code == 404
    assert student.get("/api/v1/auth/me", headers=header).json()["role"] == "student"


def test_students_cannot_write_on_behalf_of_others(
    app_and_clients: tuple[object, dict[str, TestClient], dict[str, str], str],
) -> None:
    _, clients, csrf, _ = app_and_clients
    body = {"problem_slug": "lower-bound", "source": "int y;", "user_id": "owner"}
    # The submission body has no owner field; an extra field is rejected, not honoured.
    r = clients["other_student"].post(
        "/api/v1/submissions", json=body, headers={CSRF_HEADER: csrf["other_student"]}
    )
    assert r.status_code == 422
    # Another session's CSRF token does not work with this session.
    r = clients["other_student"].post(
        "/api/v1/submissions",
        json={"problem_slug": "lower-bound", "source": "int y;"},
        headers={CSRF_HEADER: csrf["owner"]},
    )
    assert r.status_code == 403


def test_every_api_route_needs_login(
    app_and_clients: tuple[object, dict[str, TestClient], dict[str, str], str],
) -> None:
    """Guard for future endpoints: an anonymous request to any non-public route is refused."""
    app, clients, _, _ = app_and_clients
    anonymous = clients["anonymous"]
    checked = 0
    for route in app.routes:  # type: ignore[attr-defined]
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/"):
            continue
        path = re.sub(r"\{[^}]+\}", "x", route.path)
        for method in (route.methods or set()) - {"HEAD", "OPTIONS"}:
            if (method, route.path) in PUBLIC:
                continue
            r = anonymous.request(method, path, json={})
            assert r.status_code == 401, (method, route.path, r.status_code)
            checked += 1
    assert checked >= 10
