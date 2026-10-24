"""Process-wide logging setup: one JSON object per line in production, text elsewhere.

Log records never carry submission source, passwords, session or CSRF tokens. Request logs
carry the request id that the API also returns in `X-Request-ID`, so a user's error report
can be matched to the server's record.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

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
        JsonFormatter()
        if fmt == "json"
        else logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root.addHandler(handler)
    root.setLevel(os.environ.get("CODEADAPT_LOG_LEVEL", "INFO").upper())
