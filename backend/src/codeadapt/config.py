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
    # Recommendation policy version the worker uses (ADR-038): "1.5", or "1.4" to keep the
    # earlier ranking.
    policy_version: str = "1.5"
    # ADR-040: Host names the API answers to (TrustedHostMiddleware). Required in production;
    # empty elsewhere means "no Host check" (dev and test clients use arbitrary hosts).
    allowed_hosts: tuple[str, ...] = ()
    # ADR-040: the only way to run student code outside gVisor in production. Set to
    # "local-demo-only" by compose.demo.yaml; never for a deployment students can reach.
    allow_runc_in_production: bool = False

    @property
    def secure_cookies(self) -> bool:
        """Session cookies carry `Secure` everywhere except plain-HTTP dev and test."""
        return self.env is Environment.PRODUCTION

    @property
    def dev_auth_enabled(self) -> bool:
        """Stub single-user auth (ADR-007). Never available in production."""
        return self.env in (Environment.DEV, Environment.TEST)

    @property
    def docs_enabled(self) -> bool:
        """Interactive API docs and the OpenAPI document are served outside production only."""
        return self.env is not Environment.PRODUCTION

    def require_api_config(self) -> None:
        """Startup check for the API process (ADR-040): names what is missing, never values."""
        if self.env is not Environment.PRODUCTION:
            return
        if not self.allowed_hosts:
            raise ConfigError(
                "CODEADAPT_ALLOWED_HOSTS is required in production "
                "(comma-separated host names the API is served under)"
            )
        if "*" in self.allowed_hosts:
            raise ConfigError("CODEADAPT_ALLOWED_HOSTS must not contain '*' in production")

    @classmethod
    def from_env(cls) -> Settings:
        env = _environment(os.environ.get("CODEADAPT_ENV"))
        default_db = "" if env is Environment.PRODUCTION else "sqlite:///./codeadapt-dev.sqlite3"
        database_url = os.environ.get("CODEADAPT_DATABASE_URL") or default_db
        if not database_url:
            raise ConfigError(
                "CODEADAPT_DATABASE_URL is required in production"
                + ("" if "CODEADAPT_ENV" in os.environ else _UNSET_ENV_HINT)
            )
        return cls(
            env=env,
            database_url=database_url,
            content_dir=default_content_dir(),
            worker_poll_seconds=float(os.environ.get("CODEADAPT_WORKER_POLL_SECONDS", "1.0")),
            session_hours=float(os.environ.get("CODEADAPT_SESSION_HOURS", "12")),
            submissions_per_minute=_optional_int(
                os.environ.get("CODEADAPT_SUBMISSIONS_PER_MINUTE"),
                default=10 if env is Environment.PRODUCTION else None,
            ),
            policy_version=os.environ.get("CODEADAPT_POLICY_VERSION", "1.5"),
            allowed_hosts=tuple(
                h.strip()
                for h in os.environ.get("CODEADAPT_ALLOWED_HOSTS", "").split(",")
                if h.strip()
            ),
            allow_runc_in_production=_allow_runc(os.environ.get("CODEADAPT_SANDBOX_ALLOW_RUNC")),
        )


def default_content_dir() -> Path:
    return Path(os.environ.get("CODEADAPT_CONTENT_DIR") or str(_REPO_ROOT / "content" / "demo"))


class ConfigError(RuntimeError):
    """Missing or invalid configuration. Messages name variables, never their values."""


_UNSET_ENV_HINT = (
    " (CODEADAPT_ENV is not set, so production rules apply; "
    "set CODEADAPT_ENV=dev for local development)"
)
ALLOW_RUNC_VALUE = "local-demo-only"


def _environment(raw: str | None) -> Environment:
    """Fail closed (ADR-040): unset means production, an unknown value is an error. The
    development auth stub is reachable only through an explicit CODEADAPT_ENV=dev or test."""
    if raw is None or raw.strip() == "":
        return Environment.PRODUCTION
    try:
        return Environment(raw.strip())
    except ValueError:
        valid = ", ".join(e.value for e in Environment)
        raise ConfigError(f"CODEADAPT_ENV must be one of: {valid}") from None


def _allow_runc(raw: str | None) -> bool:
    if raw is None or raw == "":
        return False
    if raw != ALLOW_RUNC_VALUE:
        raise ConfigError(
            f"CODEADAPT_SANDBOX_ALLOW_RUNC accepts only {ALLOW_RUNC_VALUE!r} (or unset)"
        )
    return True


def _optional_int(value: str | None, *, default: int | None) -> int | None:
    if value is None or value == "":
        return default
    return None if value.lower() == "none" else int(value)
