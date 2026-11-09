"""Checks on the deployment files (deploy/) that need no Docker and no host."""

from __future__ import annotations

import re
from pathlib import Path

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
            if m := re.match(
                r"\s*FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?", line, re.I
            ):
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


# ---------------------------------------------------------------- R5: database TLS


def test_every_database_url_in_the_compose_files_verifies_tls() -> None:
    urls = [
        m.group(0)
        for path in DEPLOY.glob("compose.*.yaml")
        for m in re.finditer(r"postgresql\+psycopg://\S+", path.read_text())
    ]
    assert len(urls) == 5  # api, migrate, db-setup, admin, worker
    for url in urls:
        assert "sslmode=verify-full" in url and "sslrootcert=/etc/codeadapt/db-ca.crt" in url


def test_postgres_requires_tls_for_every_tcp_connection() -> None:
    compose = (DEPLOY / "compose.app.yaml").read_text()
    for setting in (
        "ssl=on",
        "ssl_min_protocol_version=TLSv1.2",
        "hba_file=/etc/postgresql/pg_hba.conf",
    ):
        assert f"- {setting}" in compose
    rules = [
        line.split()
        for line in (DEPLOY / "db" / "pg_hba.conf").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    # Only the container's own socket, TLS connections, and a refusal of everything else.
    assert rules == [
        ["local", "all", "all", "trust"],
        ["hostssl", "all", "all", "all", "scram-sha-256"],
        ["hostnossl", "all", "all", "all", "reject"],
    ]


def test_the_runner_reaches_the_database_by_its_certificate_name() -> None:
    runner = (DEPLOY / "compose.runner.yaml").read_text()
    assert '"${DB_TLS_NAME:?}:${DB_HOST:?}"' in runner  # extra_hosts
    assert "${DB_CA_FILE:?}:/etc/codeadapt/db-ca.crt:ro" in runner


# ---------------------------------------------------------------- Milestone 4: Azure hosts

WORKFLOWS = REPO_ROOT / ".github" / "workflows"
HOST = DEPLOY / "host"


def _ci_env(name: str) -> str:
    m = re.search(rf'^\s*{name}:\s*"?([0-9a-f]+)"?\s*$', (WORKFLOWS / "ci.yml").read_text(), re.M)
    assert m, f"{name} not found in ci.yml"
    return m.group(1)


def test_the_host_gvisor_install_uses_the_ci_pin() -> None:
    """The runner VM gets exactly the gVisor release the sandbox-gvisor CI job tests."""
    script = (HOST / "install-gvisor.sh").read_text()
    release, sha512 = _ci_env("GVISOR_RELEASE"), _ci_env("GVISOR_SHA512")
    assert f'GVISOR_RELEASE="{release}"' in script
    assert f'GVISOR_SHA512="{sha512}"' in script
    assert "sha512sum -c" in script
    assert f"release-{release}.0" in (HOST / "verify-host.sh").read_text()


def test_the_runner_images_are_x86_64_only() -> None:
    """Fingerprints were measured on x86-64: never ship an Arm worker or sandbox."""
    workflow = (WORKFLOWS / "release-images.yml").read_text()
    builds = dict(re.findall(r"- name: (\w+)\n(?:\s+\w+: .*\n)*?\s+platforms: (\S+)", workflow))
    assert builds == {
        "api": "linux/arm64,linux/amd64",
        "proxy": "linux/arm64,linux/amd64",
        "worker": "linux/amd64",
        "sandbox": "linux/amd64",
    }
    assert "uname -m" in (HOST / "install-gvisor.sh").read_text()


def test_pulled_images_get_the_names_the_compose_files_and_worker_use() -> None:
    from codeadapt.execution.docker import DEFAULT_IMAGE

    script = (DEPLOY / "pull-images.sh").read_text()
    assert f'SANDBOX) echo "{DEFAULT_IMAGE}"' in script
    for name in ("api", "proxy", "worker"):
        assert f"codeadapt-{name}:$image_tag" in script
        compose = "compose.runner.yaml" if name == "worker" else "compose.app.yaml"
        assert f"codeadapt-{name}:${{IMAGE_TAG" in (DEPLOY / compose).read_text()
    # Only digests: a tag alone could be re-pushed.
    assert "@sha256:[0-9a-f]{64}$" in script


def test_the_runner_firewall_closes_egress_and_metadata() -> None:
    script = (HOST / "firewall.sh").read_text()
    runner = script.split("apply_runner() {")[1].split("\n}\n")[0]
    # Containers: the database port only, then drop.
    containers = runner.split("chain OUTPUT")[0]
    assert '-p tcp -d "$db_host" --dport 5432 -j RETURN' in containers
    assert containers.rstrip().endswith("iptables -A $c -j DROP")
    # Host: closes with REJECT; 80/443 only behind the maintenance flag.
    out = runner.split("chain OUTPUT CODEADAPT-OUT")[1].split("chain INPUT")[0]
    assert out.rstrip().endswith("iptables -A $o -j REJECT")
    assert "if [ -e $MAINT_FLAG ]; then" in out
    app = script.split("apply_app() {")[1].split("\n}\n")[0]
    assert "-d $METADATA -j DROP" in app


def test_the_example_runner_runs_one_sandbox_at_a_time() -> None:
    """1 GiB runner VM: each sandbox may use 256 MiB plus gVisor's own memory (D5)."""
    assert "SANDBOX_MAX_CONCURRENCY=1" in (DEPLOY / "runner.env.example").read_text()


@pytest.mark.parametrize(
    "path",
    [DEPLOY / "pull-images.sh", *sorted(HOST.glob("*.sh"))],
    ids=lambda p: p.name,
)
def test_host_scripts_are_executable(path: Path) -> None:
    assert path.stat().st_mode & 0o111
