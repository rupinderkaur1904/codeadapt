"""Application settings, read once from `CODEADAPT_*` environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Environment(StrEnum):
    DEV = "dev"
    TEST = "test"
    PRODUCTION = "production"


@dataclass(frozen=True)
class Settings:
    env: Environment
    database_url: str
    content_dir: Path
    worker_poll_seconds: float = 1.0
    job_lease_seconds: float = 600.0
    job_max_attempts: int = 3
    # ADR-029: login sessions and request limits.
    session_hours: float = 12.0
    login_max_failures: int = 5  # per username or per client, within the window below
    login_failure_window_minutes: float = 15.0
    # Submissions one user may create per minute; None = unlimited (dev and test default).
    submissions_per_minute: int | None = None

    @property
    def secure_cookies(self) -> bool:
        """Session cookies carry `Secure` everywhere except plain-HTTP dev and test."""
        return self.env is Environment.PRODUCTION

    @property
    def dev_auth_enabled(self) -> bool:
        """Stub single-user auth (ADR-007). Never available in production."""
        return self.env in (Environment.DEV, Environment.TEST)

    @classmethod
    def from_env(cls) -> Settings:
        env = Environment(os.environ.get("CODEADAPT_ENV", "dev"))
        default_db = "" if env is Environment.PRODUCTION else "sqlite:///./codeadapt-dev.sqlite3"
        database_url = os.environ.get("CODEADAPT_DATABASE_URL") or default_db
        if not database_url:
            raise RuntimeError("CODEADAPT_DATABASE_URL is required in production")
        return cls(
            env=env,
            database_url=database_url,
            content_dir=Path(
                os.environ.get("CODEADAPT_CONTENT_DIR") or str(_REPO_ROOT / "content" / "demo")
            ),
            worker_poll_seconds=float(os.environ.get("CODEADAPT_WORKER_POLL_SECONDS", "1.0")),
            session_hours=float(os.environ.get("CODEADAPT_SESSION_HOURS", "12")),
            submissions_per_minute=_optional_int(
                os.environ.get("CODEADAPT_SUBMISSIONS_PER_MINUTE"),
                default=10 if env is Environment.PRODUCTION else None,
            ),
        )


def _optional_int(value: str | None, *, default: int | None) -> int | None:
    if value is None or value == "":
        return default
    return None if value.lower() == "none" else int(value)
