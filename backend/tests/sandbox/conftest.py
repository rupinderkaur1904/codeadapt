"""Fixtures for tests that execute real code in the Docker sandbox.

When Docker or the sandbox image is unavailable these tests are *skipped with a reason*,
unless CODEADAPT_REQUIRE_SANDBOX=1 (set in CI), in which case they fail.
"""

from __future__ import annotations

import os

import pytest

from codeadapt.execution import DockerSandbox, DockerSandboxConfig, SandboxUnavailableError


@pytest.fixture(scope="session")
async def sandbox() -> DockerSandbox:
    sb = DockerSandbox(DockerSandboxConfig.from_env())
    try:
        await sb.check_available()
    except SandboxUnavailableError as exc:
        if os.environ.get("CODEADAPT_REQUIRE_SANDBOX") == "1":
            pytest.fail(f"sandbox required but unavailable: {exc}")
        pytest.skip(f"sandbox unavailable: {exc}")
    return sb


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "tests/sandbox" in str(item.path):
            item.add_marker(pytest.mark.sandbox)
