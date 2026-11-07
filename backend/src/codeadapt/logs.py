"""Process-wide logging setup: one JSON object per line in production, text elsewhere.

Log records never carry submission source, passwords, session or CSRF tokens. Request logs
carry the request id that the API also returns in `X-Request-ID`, so a user's error report
can be matched to the server's record.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import UTC, datetime
from typing import Any

# Redaction (ADR-042) is a safety net under the rule above, not a replacement for it. It
# masks credentials that could reach a log line through an exception message or a
# third-party library: passwords in database URLs, cookie and CSRF values, and
# `password=...`-style pairs (in text, query-string or JSON form).
MASK = "***"
# Names of keys whose values are masked (not secrets themselves).
_SECRET_KEYS = "|".join(
    (
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        r"csrf[_-]?token",
        "x-csrf-token",
        r"api[_-]?key",
        "authorization",
        "cookie",
        "set-cookie",
        "codeadapt_session",
    )
)
_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # scheme://user:password@host -> scheme://user:***@host
    (re.compile(r"([a-z][a-z0-9+.-]*://[^\s:/@]+:)[^\s@/]+@", re.I), rf"\1{MASK}@"),
    # "key": "a quoted value, spaces and escapes included"
    (
        re.compile(rf"""(["']\b(?:{_SECRET_KEYS})\b["']\s*:\s*")(?:[^"\\]|\\.)*"?""", re.I),
        rf'\1{MASK}"',
    ),
    # key=value, key: value (the value ends at a delimiter); skips values already masked
    (
        re.compile(
            rf"""(["']?\b(?:{_SECRET_KEYS})\b["']?\s*[=:]\s*["']?)(?!\*\*\*)[^\s"',;&}}]+""",
            re.I,
        ),
        rf"\1{MASK}",
    ),
)


def redact(text: str) -> str:
    """Mask credentials in ``text``. Idempotent."""
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class RedactingFormatter(logging.Formatter):
    """Wraps another formatter and redacts the message, every extra string field and the
    traceback before the inner formatter renders them (so JSON escaping cannot hide a
    value from the patterns)."""

    def __init__(self, inner: logging.Formatter) -> None:
        super().__init__()
        self.inner = inner

    def format(self, record: logging.LogRecord) -> str:
        clean = logging.makeLogRecord(record.__dict__)
        clean.msg, clean.args = redact(record.getMessage()), None
        if record.exc_info:
            clean.exc_text = redact(self.inner.formatException(record.exc_info))
            clean.exc_info = None
        for key, value in record.__dict__.items():
            if key not in _STANDARD and isinstance(value, str):
                setattr(clean, key, redact(value))
        return redact(self.inner.format(clean))


# Attributes every LogRecord has; anything else was passed with `extra=` and is logged.
_STANDARD = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        entry.update({k: v for k, v in record.__dict__.items() if k not in _STANDARD})
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        elif record.exc_text:
            entry["exception"] = record.exc_text
        return json.dumps(entry, default=str)


def configure(production: bool) -> None:
    """Install one handler on the root logger, once. `CODEADAPT_LOG_FORMAT` (json|text)
    overrides the default (json in production, text otherwise)."""
    root = logging.getLogger()
    if any(getattr(h, "_codeadapt", False) for h in root.handlers):
        return
    fmt = os.environ.get("CODEADAPT_LOG_FORMAT") or ("json" if production else "text")
    handler = logging.StreamHandler()
    handler._codeadapt = True  # type: ignore[attr-defined]
    handler.setFormatter(
        RedactingFormatter(
            JsonFormatter()
            if fmt == "json"
            else logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    )
    root.addHandler(handler)
    root.setLevel(os.environ.get("CODEADAPT_LOG_LEVEL", "INFO").upper())
