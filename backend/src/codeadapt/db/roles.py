"""Least-privilege PostgreSQL roles for a deployment (ADR-042, Milestone 3).

Three roles:

- the *owner* role (the one migrations run as) owns the schema; nothing else uses it;
- the *API* role reads and writes application tables, with no DDL. It may add to the audit
  log but never change or delete it, and it may read the schema revision but never write
  it (owner decision R7, Gate B, 2026-11-07). Erasing a learner, which scrubs audit rows,
  therefore runs as the owner (`codeadapt-admin` through the `admin` Compose service);
- the *worker* role, used on the runner host whose Docker socket is root-equivalent
  (docs/deployment/milestone-3-architecture.md §4), gets only what the job pipeline uses.
  It cannot read accounts, password hashes, sessions or the audit log.

`codeadapt-admin db-grants` prints these statements for `psql`. They are idempotent and
must be re-run after a migration adds a table (the worker's list is explicit on purpose).
"""

from __future__ import annotations

from typing import Any

# The worker reads and writes these; see worker/, content/catalogue.py and db/queue.py.
WORKER_READ = (
    "alembic_version",
    "problem_versions",
    "environments",
    "fingerprint_sets",
    "submissions",
    "jobs",
    "execution_runs",
    "test_observations",
    "diagnoses",
    "recommendations",
    "followup_evaluations",
)
WORKER_INSERT = (
    "problem_versions",  # catalogue sync at start-up
    "environments",
    "fingerprint_sets",
    "execution_runs",
    "test_observations",
    "diagnoses",
    "recommendations",
    "followup_evaluations",
)
WORKER_UPDATE = ("jobs",)
# Never granted to the worker.
WORKER_DENIED = ("users", "auth_sessions", "audit_events")
# R7: the API role may only append to these (audit_events) or only read them
# (alembic_version). A compromised API process cannot erase the access log or fake the
# schema revision.
API_APPEND_ONLY = ("audit_events",)
API_READ_ONLY = ("alembic_version",)


def _ident(name: str) -> str:
    if not name.replace("_", "").isalnum():
        raise ValueError(f"unsafe role name: {name!r}")
    return f'"{name}"'


def grant_statements(api_role: str, worker_role: str, schema: str = "public") -> list[str]:
    api, worker, sch = _ident(api_role), _ident(worker_role), _ident(schema)
    statements = [
        f"REVOKE CREATE ON SCHEMA {sch} FROM PUBLIC",
        f"GRANT USAGE ON SCHEMA {sch} TO {api}, {worker}",
        # API: data access on every table, no DDL.
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {sch} TO {api}",
        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {sch} TO {api}",
        # R7: no rewriting of the access log, no writes to the schema revision.
        *(
            f"REVOKE UPDATE, DELETE, TRUNCATE ON {sch}.{_ident(t)} FROM {api}"
            for t in API_APPEND_ONLY
        ),
        *(
            f"REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON {sch}.{_ident(t)} FROM {api}"
            for t in API_READ_ONLY
        ),
        # Worker: start from nothing, then the explicit lists.
        f"REVOKE ALL ON ALL TABLES IN SCHEMA {sch} FROM {worker}",
        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {sch} TO {worker}",
    ]
    statements += [f"GRANT SELECT ON {sch}.{_ident(t)} TO {worker}" for t in WORKER_READ]
    statements += [f"GRANT INSERT ON {sch}.{_ident(t)} TO {worker}" for t in WORKER_INSERT]
    statements += [f"GRANT UPDATE ON {sch}.{_ident(t)} TO {worker}" for t in WORKER_UPDATE]
    return statements


def setup_roles(
    connection: Any, roles_and_passwords: dict[str, str], api_role: str, worker_role: str
) -> None:
    """Create or update the login roles, then apply the grants (run as the schema owner).

    ``connection`` is a SQLAlchemy connection on psycopg 3. Passwords are passed as quoted
    literals built by psycopg (PostgreSQL takes no bind parameters in ROLE statements) and
    never logged: engines hide parameters (ADR-042) and statements are not echoed.
    """
    from psycopg import sql

    raw = connection.connection.driver_connection
    with raw.cursor() as cursor:
        for role, password in roles_and_passwords.items():
            _ident(role)
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,))
            verb = "ALTER" if cursor.fetchone() else "CREATE"
            cursor.execute(
                sql.SQL(verb + " ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )
    for statement in grant_statements(api_role, worker_role):
        connection.exec_driver_sql(statement)
