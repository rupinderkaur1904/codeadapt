"""Structured logs: JSON lines with the request id, and no secrets."""

import json
import logging

import pytest
from fastapi.testclient import TestClient

from codeadapt.api.app import create_app
from codeadapt.config import Settings
from codeadapt.logs import JsonFormatter


def test_json_formatter_keeps_extra_fields_and_exceptions() -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        record = logging.LogRecord("x", logging.ERROR, __file__, 1, "failed %s", ("job",), None)
        record.exc_info = (type(exc), exc, exc.__traceback__)
    record.request_id = "abc"
    entry = json.loads(JsonFormatter().format(record))
    assert entry["message"] == "failed job"
    assert entry["level"] == "ERROR"
    assert entry["request_id"] == "abc"
    assert "RuntimeError: boom" in entry["exception"]


def test_requests_are_logged_with_their_id_and_without_query_or_body(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    client = TestClient(create_app(settings))
    with caplog.at_level(logging.INFO, logger="codeadapt.api"):
        r = client.post(
            "/api/v1/auth/login?next=secret-query",
            json={"username": "nobody", "password": "hunter2-password"},
        )
    assert r.status_code == 401
    (record,) = [rec for rec in caplog.records if getattr(rec, "path", "") == "/api/v1/auth/login"]
    assert record.request_id == r.headers["X-Request-ID"]  # type: ignore[attr-defined]
    assert record.status == 401  # type: ignore[attr-defined]
    text = JsonFormatter().format(record)
    assert "hunter2" not in text
    assert "secret-query" not in text
