"""Checks on the deployment files (deploy/) that need no Docker and no host."""

from __future__ import annotations

import re

import pytest

from tests.paths import REPO_ROOT

DEPLOY = REPO_ROOT / "deploy"
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")


def _external_images() -> list[tuple[str, str]]:
    """(file, image reference) for every image pulled from a registry."""
    found: list[tuple[str, str]] = []
    for path in [*DEPLOY.glob("*.Dockerfile"), REPO_ROOT / "sandbox" / "Dockerfile"]:
        stages: set[str] = set()
        for line in path.read_text().splitlines():
            if m := re.match(r"\s*FROM\s+(\S+)(?:\s+AS\s+(\S+))?", line, re.I):
                if m.group(1) not in stages:
                    found.append((path.name, m.group(1)))
                if m.group(2):
                    stages.add(m.group(2))
            elif m := re.match(r"\s*COPY\s+--from=(\S+)", line, re.I):
                if m.group(1) not in stages:
                    found.append((path.name, m.group(1)))
    for path in DEPLOY.glob("compose.*.yaml"):
        for m in re.finditer(r"^\s*image:\s*(\S+)", path.read_text(), re.M):
            if not m.group(1).startswith("codeadapt-"):  # built here from pinned bases
                found.append((path.name, m.group(1)))
    return found


def test_the_check_sees_every_base_image() -> None:
    names = {ref.split(":")[0] for _, ref in _external_images()}
    assert {"python", "docker", "node", "caddy", "postgres", "gcc"} <= names


@pytest.mark.parametrize(("file", "ref"), _external_images())
def test_every_base_image_is_pinned_by_digest(file: str, ref: str) -> None:
    """R6 (owner, Gate B): a re-pushed tag cannot change what gets built or run."""
    assert DIGEST.search(ref), f"{file}: {ref} is not pinned to an @sha256 digest"


def test_the_runbook_records_every_digest() -> None:
    runbook = (REPO_ROOT / "docs" / "deployment" / "production-runbook.md").read_text()
    for _, ref in _external_images():
        assert ref in runbook, f"{ref} is missing from the runbook's image table"
