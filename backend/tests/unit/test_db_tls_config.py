"""R5 (owner decision, Gate B): PostgreSQL TLS from a private CA, checked without a server.

The connection tests against a real TLS-enabled PostgreSQL are in tests/tls/ and run in
CI against the production Compose stack.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from codeadapt.config import ConfigError, Environment, Settings
from codeadapt.worker.main import require_database_tls
from tests.paths import REPO_ROOT

SCRIPT = REPO_ROOT / "deploy" / "db-tls" / "make-db-certs.sh"
PG = "postgresql+psycopg://w:pw@db.codeadapt.internal:5432/codeadapt"
needs_openssl = pytest.mark.skipif(shutil.which("openssl") is None, reason="needs openssl")


@pytest.fixture
def ca_file(tmp_path: Path) -> Path:
    path = tmp_path / "ca.crt"
    path.write_text("-----BEGIN CERTIFICATE-----\n")
    return path


@pytest.mark.parametrize(
    "query",
    [
        "",  # libpq's default (prefer) silently falls back to plain text
        "?sslmode=require",  # encrypts but trusts any certificate: open to interception
        "?sslmode=verify-ca&sslrootcert={ca}",  # checks the CA but not the host name
        "?sslmode=verify-full",  # no CA given
        "?sslmode=verify-full&sslrootcert=/nonexistent/ca.crt",
    ],
)
def test_production_worker_refuses_a_database_url_without_verified_tls(
    settings: Settings, ca_file: Path, query: str
) -> None:
    prod = replace(settings, env=Environment.PRODUCTION, database_url=PG + query.format(ca=ca_file))
    with pytest.raises(ConfigError, match=r"sslmode=verify-full|sslrootcert"):
        require_database_tls(prod)


def test_production_worker_accepts_verify_full_with_a_ca_file(
    settings: Settings, ca_file: Path
) -> None:
    url = f"{PG}?sslmode=verify-full&sslrootcert={ca_file}"
    require_database_tls(replace(settings, env=Environment.PRODUCTION, database_url=url))


def test_the_guard_leaves_sqlite_and_development_alone(settings: Settings) -> None:
    demo = "sqlite:////data/codeadapt-demo.sqlite3"  # compose.demo.yaml
    require_database_tls(replace(settings, env=Environment.PRODUCTION, database_url=demo))
    require_database_tls(replace(settings, env=Environment.DEV, database_url=PG))


def _openssl(*args: str) -> str:
    return subprocess.run(["openssl", *args], capture_output=True, text=True, check=True).stdout


@needs_openssl
def test_make_db_certs_issues_a_server_certificate_for_both_names(tmp_path: Path) -> None:
    out = tmp_path / "tls"
    subprocess.run(["bash", str(SCRIPT), str(out), "db.codeadapt.internal"], check=True)
    _openssl("verify", "-CAfile", str(out / "ca.crt"), str(out / "server.crt"))
    san = _openssl("x509", "-in", str(out / "server.crt"), "-noout", "-ext", "subjectAltName")
    assert "DNS:db.codeadapt.internal" in san and "DNS:db" in san
    assert "IP Address" not in san  # clients must use a name, which verify-full checks
    usage = _openssl("x509", "-in", str(out / "server.crt"), "-noout", "-ext", "extendedKeyUsage")
    assert "TLS Web Server Authentication" in usage
    ca = _openssl("x509", "-in", str(out / "ca.crt"), "-noout", "-ext", "basicConstraints")
    assert "CA:TRUE" in ca
    assert (out / "ca.key").stat().st_mode & 0o777 == 0o600
    assert (out / "server.key").stat().st_mode & 0o777 == 0o640
    assert {p.name for p in out.iterdir()} == {"ca.crt", "ca.key", "server.crt", "server.key"}


@needs_openssl
def test_a_certificate_from_another_ca_does_not_verify(tmp_path: Path) -> None:
    ours, theirs = tmp_path / "ours", tmp_path / "theirs"
    for out in (ours, theirs):
        subprocess.run(["bash", str(SCRIPT), str(out), "db.codeadapt.internal"], check=True)
    with pytest.raises(subprocess.CalledProcessError):
        _openssl("verify", "-CAfile", str(ours / "ca.crt"), str(theirs / "server.crt"))


@needs_openssl
def test_make_db_certs_never_overwrites_and_checks_the_name(tmp_path: Path) -> None:
    out = tmp_path / "tls"
    subprocess.run(["bash", str(SCRIPT), str(out), "db.codeadapt.internal"], check=True)
    before = (out / "ca.key").read_bytes()
    again = subprocess.run(
        ["bash", str(SCRIPT), str(out), "db.codeadapt.internal"], capture_output=True, check=False
    )
    assert again.returncode != 0 and (out / "ca.key").read_bytes() == before
    bad = subprocess.run(
        ["bash", str(SCRIPT), str(tmp_path / "x"), "db;rm -rf /"], capture_output=True, check=False
    )
    assert bad.returncode == 2
