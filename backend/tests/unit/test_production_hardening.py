"""ADR-040: fail-closed configuration, HTTP hardening and the production runtime rule."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from codeadapt.api.app import create_app
from codeadapt.config import ConfigError, Environment, Settings
from codeadapt.execution import SandboxUnavailableError
from codeadapt.execution.docker import DockerSandbox, DockerSandboxConfig
from codeadapt.worker.main import require_production_runtime

SECRET_URL = "postgresql+psycopg://user:hunter2-secret@db/codeadapt"  # noqa: S105 - fixture


# ---------------------------------------------------------------- environment


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for name in (
        "CODEADAPT_ENV",
        "CODEADAPT_DATABASE_URL",
        "CODEADAPT_ALLOWED_HOSTS",
        "CODEADAPT_SANDBOX_ALLOW_RUNC",
    ):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_unset_environment_means_production_not_dev(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("CODEADAPT_DATABASE_URL", "sqlite:///x.sqlite3")
    settings = Settings.from_env()
    assert settings.env is Environment.PRODUCTION
    assert not settings.dev_auth_enabled
    assert settings.secure_cookies
    assert not settings.docs_enabled


@pytest.mark.parametrize("value", ["", "  "])
def test_blank_environment_means_production(clean_env: pytest.MonkeyPatch, value: str) -> None:
    clean_env.setenv("CODEADAPT_ENV", value)
    clean_env.setenv("CODEADAPT_DATABASE_URL", "sqlite:///x.sqlite3")
    assert Settings.from_env().env is Environment.PRODUCTION


@pytest.mark.parametrize("value", ["development", "DEV", "prod", "staging"])
def test_unknown_environment_is_an_error(clean_env: pytest.MonkeyPatch, value: str) -> None:
    clean_env.setenv("CODEADAPT_ENV", value)
    with pytest.raises(ConfigError, match="CODEADAPT_ENV must be one of"):
        Settings.from_env()


@pytest.mark.parametrize("value", ["dev", "test"])
def test_dev_auth_only_with_explicit_dev_or_test(clean_env: pytest.MonkeyPatch, value: str) -> None:
    clean_env.setenv("CODEADAPT_ENV", value)
    assert Settings.from_env().dev_auth_enabled


def test_missing_database_url_is_named_and_hints_at_unset_env(
    clean_env: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ConfigError) as err:
        Settings.from_env()
    assert "CODEADAPT_DATABASE_URL" in str(err.value)
    assert "CODEADAPT_ENV is not set" in str(err.value)


def test_api_refuses_production_without_allowed_hosts(
    settings: Settings, sessions: sessionmaker[Session]
) -> None:
    prod = replace(settings, env=Environment.PRODUCTION, database_url=SECRET_URL)
    with pytest.raises(ConfigError) as err:
        prod.require_api_config()
    assert "CODEADAPT_ALLOWED_HOSTS" in str(err.value)
    assert "hunter2" not in str(err.value)
    with pytest.raises(ConfigError):
        create_app(replace(settings, env=Environment.PRODUCTION), sessions)
    with pytest.raises(ConfigError, match=r"\*"):
        replace(prod, allowed_hosts=("*",)).require_api_config()


def test_allowed_hosts_are_parsed(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("CODEADAPT_ENV", "production")
    clean_env.setenv("CODEADAPT_DATABASE_URL", "sqlite:///x.sqlite3")
    clean_env.setenv("CODEADAPT_ALLOWED_HOSTS", " codeadapt.example , localhost,")
    assert Settings.from_env().allowed_hosts == ("codeadapt.example", "localhost")


def test_runc_override_accepts_only_the_demo_value(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("CODEADAPT_ENV", "dev")
    assert not Settings.from_env().allow_runc_in_production
    clean_env.setenv("CODEADAPT_SANDBOX_ALLOW_RUNC", "local-demo-only")
    assert Settings.from_env().allow_runc_in_production
    for value in ("1", "true", "yes"):
        clean_env.setenv("CODEADAPT_SANDBOX_ALLOW_RUNC", value)
        with pytest.raises(ConfigError, match="local-demo-only"):
            Settings.from_env()


# ---------------------------------------------------------------- HTTP


@pytest.fixture
def prod_client(settings: Settings, sessions: sessionmaker[Session]) -> TestClient:
    prod = replace(settings, env=Environment.PRODUCTION, allowed_hosts=("testserver",))
    return TestClient(create_app(prod, sessions), base_url="https://testserver")


@pytest.fixture
def client(settings: Settings, sessions: sessionmaker[Session]) -> TestClient:
    return TestClient(create_app(settings, sessions))


def test_security_headers_on_success_and_error_responses(prod_client: TestClient) -> None:
    for path in ("/api/v1/health", "/api/v1/problems", "/api/v1/nope"):
        h = prod_client.get(path).headers
        assert h["x-content-type-options"] == "nosniff"
        assert h["x-frame-options"] == "DENY"
        assert h["referrer-policy"] == "no-referrer"
        assert h["cache-control"] == "no-store"
        assert h["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
        assert h["strict-transport-security"] == "max-age=31536000"


def test_no_hsts_outside_production(client: TestClient) -> None:
    h = client.get("/api/v1/health").headers
    assert "strict-transport-security" not in h
    assert h["x-content-type-options"] == "nosniff"


def test_docs_and_schema_are_off_in_production(prod_client: TestClient, client: TestClient) -> None:
    for path in ("/api/docs", "/api/redoc", "/api/openapi.json"):
        assert prod_client.get(path).status_code == 404
    assert client.get("/api/openapi.json").status_code == 200


def test_unknown_host_is_refused_in_production(prod_client: TestClient) -> None:
    r = prod_client.get("/api/v1/health", headers={"Host": "evil.example"})
    assert r.status_code == 400
    assert r.headers["x-content-type-options"] == "nosniff"
    assert prod_client.get("/api/v1/health").status_code == 200


def test_oversized_bodies_are_refused(prod_client: TestClient) -> None:
    big = b"x" * (1024 * 1024 + 1)
    r = prod_client.post(
        "/api/v1/auth/login", content=big, headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 413, r.text

    def chunks() -> Iterator[bytes]:  # no Content-Length: counted as it arrives
        for _ in range(17):
            yield b"x" * 65536

    r = prod_client.post(
        "/api/v1/auth/login", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 413


# ---------------------------------------------------------------- worker runtime


class _FakeSandbox(DockerSandbox):
    def __init__(self, runtime: str | None, registered: set[str]) -> None:
        super().__init__(DockerSandboxConfig(runtime=runtime))
        self._registered = registered

    async def registered_runtimes(self) -> set[str]:
        return self._registered


def _check(settings: Settings, sandbox: DockerSandbox) -> None:
    asyncio.run(require_production_runtime(settings, sandbox))


def test_production_worker_refuses_runc(settings: Settings) -> None:
    prod = replace(settings, env=Environment.PRODUCTION)
    for runtime in (None, "runc", "crun"):
        with pytest.raises(ConfigError, match="runsc"):
            _check(prod, _FakeSandbox(runtime, {"runc", "runsc"}))


def test_production_worker_refuses_unregistered_runsc(settings: Settings) -> None:
    prod = replace(settings, env=Environment.PRODUCTION)
    with pytest.raises(SandboxUnavailableError, match="not registered"):
        _check(prod, _FakeSandbox("runsc", {"runc"}))


def test_production_worker_accepts_registered_runsc(settings: Settings) -> None:
    prod = replace(settings, env=Environment.PRODUCTION)
    sandbox = _FakeSandbox("runsc", {"runc", "runsc"})
    _check(prod, sandbox)
    # Every container is started with the explicit runtime: Docker cannot fall back to runc.
    args = sandbox._hardening(memory_mib=64, pids=8, open_files=32, cpu_seconds=1, fsize=0)
    assert args[args.index("--runtime") + 1] == "runsc"


def test_runc_in_production_only_with_the_explicit_demo_override(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    demo = replace(settings, env=Environment.PRODUCTION, allow_runc_in_production=True)
    _check(demo, _FakeSandbox(None, {"runc"}))
    assert "WITHOUT gVisor" in caplog.text


def test_dev_worker_keeps_the_local_runtime(settings: Settings) -> None:
    _check(settings, _FakeSandbox(None, {"runc"}))  # TEST env: unchanged behaviour
