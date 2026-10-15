from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from codeadapt.api.app import create_app
from codeadapt.config import Environment, Settings

STUDENT = {"X-Dev-Role": "student"}
RESEARCHER = {"X-Dev-Role": "researcher"}


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


def test_list_and_get_problem_exposes_only_samples(client: TestClient) -> None:
    problems = client.get("/api/v1/problems", headers=STUDENT).json()
    assert [p["slug"] for p in problems] == ["lower-bound"]
    detail = client.get("/api/v1/problems/lower-bound", headers=STUDENT).json()
    assert "lower_bound_index" in detail["interface"]
    assert len(detail["sample_tests"]) == 2
    text = str(detail)
    for secret in ("harness", "reference", "error_model", "upper_bound_confusion", "D 200000"):
        assert secret not in text


def test_submission_lifecycle_until_worker_runs(client: TestClient) -> None:
    accepted = client.post(
        "/api/v1/submissions",
        json={"problem_slug": "lower-bound", "source": "int x;"},
        headers=STUDENT,
    )
    assert accepted.status_code == 202
    sub_id = accepted.json()["id"]
    view = client.get(f"/api/v1/submissions/{sub_id}", headers=STUDENT).json()
    assert view["status"] == "queued"
    assert view["created_at"].endswith(("Z", "+00:00"))
    assert view["feedback"] is None


def test_errors_are_problem_json(client: TestClient) -> None:
    r = client.get("/api/v1/problems/nope", headers=STUDENT)
    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["type"].endswith("/not-found")
    assert body["request_id"] == r.headers["X-Request-ID"]

    r = client.post("/api/v1/submissions", json={"problem_slug": "lower-bound"}, headers=STUDENT)
    assert r.status_code == 422
    assert r.json()["type"].endswith("/invalid-request")


def test_source_size_limit(client: TestClient) -> None:
    r = client.post(
        "/api/v1/submissions",
        json={"problem_slug": "lower-bound", "source": "x" * (64 * 1024 + 1)},
        headers=STUDENT,
    )
    assert r.status_code == 422
    assert "exceeds" in r.json()["detail"]


def test_extra_fields_rejected(client: TestClient) -> None:
    r = client.post(
        "/api/v1/submissions",
        json={"problem_slug": "lower-bound", "source": "x", "user_id": 1},
        headers=STUDENT,
    )
    assert r.status_code == 422


def test_students_cannot_see_others_submissions_or_traces(client: TestClient) -> None:
    sub_id = client.post(
        "/api/v1/submissions",
        json={"problem_slug": "lower-bound", "source": "int x;"},
        headers=RESEARCHER,
    ).json()["id"]
    assert client.get(f"/api/v1/submissions/{sub_id}", headers=STUDENT).status_code == 404
    r = client.get(f"/api/v1/research/submissions/{sub_id}/trace", headers=STUDENT)
    assert r.status_code == 403
    trace = client.get(f"/api/v1/research/submissions/{sub_id}/trace", headers=RESEARCHER)
    assert trace.status_code == 200
    assert trace.json()["job"]["state"] == "queued"


def test_dev_auth_is_disabled_in_production(settings: Settings) -> None:
    client = TestClient(create_app(replace(settings, env=Environment.PRODUCTION)))
    r = client.get("/api/v1/problems", headers=RESEARCHER)
    assert r.status_code == 503
    assert r.json()["type"].endswith("/auth-not-configured")
    assert client.get("/api/v1/health").status_code == 200


def test_starter_code_and_own_submission_history(client: TestClient) -> None:
    detail = client.get("/api/v1/problems/lower-bound", headers=STUDENT).json()
    assert (
        "int lower_bound_index(const std::vector<int>& a, int target) {" in detail["starter_code"]
    )
    ids = [
        client.post(
            "/api/v1/submissions",
            json={"problem_slug": "lower-bound", "source": f"// {i}"},
            headers=STUDENT,
        ).json()["id"]
        for i in range(3)
    ]
    client.post(
        "/api/v1/submissions",
        json={"problem_slug": "lower-bound", "source": "// other user"},
        headers=RESEARCHER,
    )
    history = client.get("/api/v1/submissions?problem_slug=lower-bound", headers=STUDENT).json()
    assert {h["id"] for h in history} == set(ids)
    assert client.get("/api/v1/submissions?problem_slug=nope", headers=STUDENT).json() == []
