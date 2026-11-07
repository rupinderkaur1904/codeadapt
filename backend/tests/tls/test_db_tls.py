"""R5 (owner decision, Gate B): connections to a real TLS-enabled PostgreSQL.

CI runs these against the production App VM stack (deploy/compose.app.yaml, with
certificates from deploy/db-tls/make-db-certs.sh and deploy/db/pg_hba.conf), as the worker
role. They need, in the environment:

    CODEADAPT_TEST_TLS_HOSTADDR   address the server listens on (127.0.0.1 in CI)
    CODEADAPT_TEST_TLS_PORT       its port
    CODEADAPT_TEST_TLS_NAME       the name in its certificate (db.codeadapt.internal)
    CODEADAPT_TEST_TLS_CA         our CA certificate
    CODEADAPT_TEST_TLS_ROGUE_CA   a CA certificate from another, unrelated private CA
    CODEADAPT_TEST_TLS_USER, CODEADAPT_TEST_TLS_PASSWORD, CODEADAPT_TEST_TLS_DBNAME

Without them the tests skip, unless CODEADAPT_TEST_TLS_REQUIRED=1 (CI), when they fail.
"""

from __future__ import annotations

import os
from dataclasses import replace
from typing import Any

import psycopg
import pytest
from sqlalchemy import text

from codeadapt.config import Environment, Settings
from codeadapt.db.session import make_engine
from codeadapt.worker.main import require_database_tls

KEYS = ("HOSTADDR", "PORT", "NAME", "CA", "ROGUE_CA", "USER", "PASSWORD", "DBNAME")
ENV = {k: os.environ.get(f"CODEADAPT_TEST_TLS_{k}", "") for k in KEYS}
MISSING = [k for k, v in ENV.items() if not v]

if MISSING and os.environ.get("CODEADAPT_TEST_TLS_REQUIRED") == "1":
    raise RuntimeError(f"TLS tests required but not configured: {MISSING}")
pytestmark = pytest.mark.skipif(bool(MISSING), reason="needs a TLS PostgreSQL (see docstring)")

SSL_STATE = "SELECT ssl, version FROM pg_stat_ssl WHERE pid = pg_backend_pid()"


def _connect(**overrides: Any) -> psycopg.Connection[Any]:
    params: dict[str, Any] = {
        "host": ENV["NAME"],
        "hostaddr": ENV["HOSTADDR"],
        "port": ENV["PORT"],
        "user": ENV["USER"],
        "password": ENV["PASSWORD"],
        "dbname": ENV["DBNAME"],
        "connect_timeout": 10,
        "sslmode": "verify-full",
        "sslrootcert": ENV["CA"],
    }
    params.update(overrides)
    return psycopg.connect(**{k: v for k, v in params.items() if v is not None})


def test_valid_certificate_and_name_give_an_encrypted_connection() -> None:
    with _connect() as conn:
        ssl, version = conn.execute(SSL_STATE).fetchone() or (None, None)
    assert ssl is True
    assert version in ("TLSv1.2", "TLSv1.3")


def test_a_server_certificate_from_another_ca_is_refused() -> None:
    """What the worker sees if anything but our database answers: an interceptor, or a
    server with a certificate from any public or private CA other than ours."""
    with pytest.raises(psycopg.OperationalError, match="certificate verify failed"):
        _connect(sslrootcert=ENV["ROGUE_CA"])


def test_a_certificate_for_another_name_is_refused() -> None:
    with pytest.raises(psycopg.OperationalError, match="does not match host name"):
        _connect(host="other.codeadapt.internal")


def test_connecting_by_address_instead_of_name_is_refused() -> None:
    with pytest.raises(psycopg.OperationalError, match="does not match host name"):
        _connect(host=ENV["HOSTADDR"], hostaddr=None)


def test_the_server_refuses_plain_text() -> None:
    with pytest.raises(psycopg.OperationalError, match="no encryption"):
        _connect(sslmode="disable", sslrootcert=None)


def test_the_workers_url_form_connects_over_verified_tls(settings: Settings) -> None:
    """The URL shape of compose.runner.yaml, through the application's own engine."""
    url = (
        f"postgresql+psycopg://{ENV['USER']}:{ENV['PASSWORD']}@{ENV['NAME']}:{ENV['PORT']}"
        f"/{ENV['DBNAME']}?sslmode=verify-full&sslrootcert={ENV['CA']}"
        f"&hostaddr={ENV['HOSTADDR']}"
    )
    require_database_tls(replace(settings, env=Environment.PRODUCTION, database_url=url))
    engine = make_engine(url)
    try:
        with engine.connect() as conn:
            assert conn.execute(text(SSL_STATE)).one()[0] is True
    finally:
        engine.dispose()
