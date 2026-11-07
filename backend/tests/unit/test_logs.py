"""Structured logs: JSON lines with the request id, and no secrets (ADR-042 redaction)."""

import io
import json
import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from codeadapt import logs
from codeadapt.api.app import create_app
from codeadapt.config import Settings
from codeadapt.db.session import make_engine
from codeadapt.logs import MASK, JsonFormatter, RedactingFormatter, redact
from codeadapt.worker.pipeline import MAX_ERROR_CHARS, _error_text


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


# ---------------------------------------------------------------- redaction (ADR-042)


@pytest.mark.parametrize(
    ("raw", "secret"),
    [
        ("postgresql+psycopg://codeadapt:hunter2@db:5432/x", "hunter2"),
        ('{"password": "correct horse battery"}', "horse"),
        ("POST /login?password=s3cret&next=1", "s3cret"),
        ("Cookie: codeadapt_session=tok123; theme=dark", "tok123"),
        ("X-CSRF-Token: abcdef123", "abcdef123"),
        ("csrf_token=zz9", "zz9"),
        ("Authorization: Bearer-xyz", "Bearer-xyz"),
    ],
)
def test_redact_masks_credentials(raw: str, secret: str) -> None:
    out = redact(raw)
    assert secret not in out
    assert MASK in out
    assert redact(out) == out  # idempotent


def test_redact_leaves_ordinary_text_alone() -> None:
    for line in ("GET /api/v1/problems 200", "session token expired", '{"message": "ok"}'):
        assert redact(line) == line


def _record_with_exception(message: str, exc: Exception) -> logging.LogRecord:
    try:
        raise exc
    except Exception as caught:
        record = logging.LogRecord("x", logging.ERROR, __file__, 1, message, (), None)
        record.exc_info = (type(caught), caught, caught.__traceback__)
    return record


@pytest.mark.parametrize("inner", [JsonFormatter(), logging.Formatter("%(message)s")])
def test_formatter_redacts_message_extras_and_traceback(inner: logging.Formatter) -> None:
    record = _record_with_exception(
        'connect failed for "password": "pw in message"',
        RuntimeError("could not connect to postgresql://u:pw-in-trace@db/x"),
    )
    record.detail = "password=pw-in-extra"
    out = RedactingFormatter(inner).format(record)
    for secret in ("pw in message", "pw-in-trace", "pw-in-extra"):
        assert secret not in out
    assert "RuntimeError" in out  # the traceback itself is kept


def test_configured_handler_redacts(monkeypatch: pytest.MonkeyPatch) -> None:
    root = logging.getLogger()
    saved = root.handlers[:]
    root.handlers = [h for h in root.handlers if not getattr(h, "_codeadapt", False)]
    try:
        monkeypatch.setenv("CODEADAPT_LOG_FORMAT", "json")
        logs.configure(production=True)
        (handler,) = [h for h in root.handlers if getattr(h, "_codeadapt", False)]
        stream = io.StringIO()
        handler.setStream(stream)  # type: ignore[attr-defined]
        logging.getLogger("codeadapt.test").error("db url postgresql://u:topsecret@h/d")
        assert "topsecret" not in stream.getvalue()
    finally:
        root.handlers = saved


def test_database_errors_do_not_carry_bound_values() -> None:
    engine = make_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE t (x TEXT UNIQUE)"))
        conn.execute(text("INSERT INTO t VALUES (:x)"), {"x": "int student_source;"})
    with pytest.raises(IntegrityError) as err, engine.begin() as conn:
        conn.execute(text("INSERT INTO t VALUES (:x)"), {"x": "int student_source;"})
    assert "student_source" not in str(err.value)
    assert "student_source" not in _error_text(err.value, with_type=True)


def test_stored_job_errors_are_redacted_and_bounded() -> None:
    stored = _error_text(RuntimeError("dsn postgresql://u:pw123@h/d " + "x" * 5000))
    assert "pw123" not in stored
    assert len(stored) == MAX_ERROR_CHARS
