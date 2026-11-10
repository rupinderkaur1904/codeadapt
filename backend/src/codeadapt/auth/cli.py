"""`codeadapt-admin`: create accounts, set passwords, disable accounts (ADR-029); back up
a SQLite database; report operational status (ADR-042).

Passwords are read from the terminal without echo, or from stdin when it is not a
terminal (one line). They are never accepted as command-line arguments, which other local
users could read from the process list.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sqlite3
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from codeadapt import auth, ops
from codeadapt.config import Settings
from codeadapt.db import roles
from codeadapt.db.models import DataClass, Role, User, utcnow
from codeadapt.db.session import make_engine, make_session_factory

_OPERATOR = "codeadapt-admin"
MIN_DB_PASSWORD_CHARS = 16
STAFF_ROLES = (Role.RESEARCHER.value, Role.ADMIN.value)


def _staff_logins(session: Session) -> list[User]:
    """Accounts that can log in and see every learner's data (ADR-045)."""
    return list(
        session.scalars(
            select(User).where(
                User.role.in_(STAFF_ROLES),
                User.password_hash.is_not(None),
                User.disabled.is_(False),
            )
        )
    )


def _read_password() -> str:
    if sys.stdin.isatty():
        first = getpass.getpass("New password: ")
        if first != getpass.getpass("Repeat: "):
            raise SystemExit("passwords differ")
        return first
    return sys.stdin.readline().rstrip("\n")


def _backup(database_url: str, destination: Path) -> int:
    """SQLite's online backup API: safe while the API and worker are running. Other
    databases are backed up with their own tools (docs/deployment.md)."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise SystemExit("backup supports SQLite only; use the database's own tool (pg_dump)")
    if destination.exists():
        raise SystemExit(f"{destination} exists; refusing to overwrite")
    source = sqlite3.connect(f"file:{database_url[len(prefix) :]}?mode=ro", uri=True)
    target = sqlite3.connect(destination)
    try:
        source.backup(target)
        (check,) = target.execute("PRAGMA integrity_check").fetchone()
        (revision,) = target.execute("SELECT version_num FROM alembic_version").fetchone()
    finally:
        target.close()
        source.close()
    if check != "ok":
        raise SystemExit(f"backup failed its integrity check: {check}")
    print(f"backup: {destination} (schema revision {revision}, integrity ok)")
    return 0


def _db_setup(database_url: str, api_role: str, worker_role: str) -> int:
    if not database_url.startswith("postgresql"):
        raise SystemExit("db-setup is for PostgreSQL deployments")
    if "CHANGE_ME" in database_url:
        raise SystemExit("the owner database password is still the example placeholder")
    passwords = {}
    for role, variable in (
        (api_role, "CODEADAPT_API_DB_PASSWORD"),
        (worker_role, "CODEADAPT_WORKER_DB_PASSWORD"),
    ):
        value = os.environ.get(variable, "")
        if len(value) < MIN_DB_PASSWORD_CHARS or value.startswith("CHANGE_ME"):
            raise SystemExit(f"{variable} must be set to a generated password")
        passwords[role] = value
    engine = make_engine(database_url)
    with engine.begin() as connection:
        roles.setup_roles(connection, passwords, api_role, worker_role)
    engine.dispose()
    print(f"db-setup: roles {api_role}, {worker_role} ready; grants applied")
    return 0


def _status(session: Session, args: argparse.Namespace) -> int:
    report = ops.collect(session, utcnow(), args.window_hours)
    problems = report.problems(
        ops.Thresholds(
            max_queue_age_seconds=args.max_queue_age_seconds,
            max_failed_jobs=args.max_failed_jobs,
            max_adaptation_failures=args.max_adaptation_failures,
        )
    )
    print(json.dumps({**report.as_dict(), "ok": not problems, "problems": problems}))
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codeadapt-admin", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-user", help="create an account and set its password")
    create.add_argument("username")
    create.add_argument("--role", choices=[r.value for r in Role], required=True)
    create.add_argument("--data-class", choices=[d.value for d in DataClass], required=True)
    create.add_argument(
        "--allow-second-staff",
        action="store_true",
        help="create a researcher or admin even though one already can log in (ADR-045)",
    )
    for name, text in (("set-password", "set a new password"), ("disable", "disable login")):
        p = sub.add_parser(name, help=f"{text}; ends the account's sessions")
        p.add_argument("username")
    sub.add_parser("list", help="list accounts")
    backup = sub.add_parser("backup", help="consistent online copy of a SQLite database")
    backup.add_argument("destination", type=Path)
    status = sub.add_parser(
        "status",
        help="queue and failure counts as JSON; exit 1 when a threshold is crossed (monitoring)",
    )
    status.add_argument("--window-hours", type=float, default=24.0)
    limits = ops.Thresholds()
    status.add_argument("--max-queue-age-seconds", type=float, default=limits.max_queue_age_seconds)
    status.add_argument("--max-failed-jobs", type=int, default=limits.max_failed_jobs)
    status.add_argument(
        "--max-adaptation-failures", type=int, default=limits.max_adaptation_failures
    )
    grants = sub.add_parser(
        "db-grants",
        help="print least-privilege PostgreSQL grants for the API and worker roles (psql)",
    )
    grants.add_argument("--api-role", default="codeadapt_api")
    grants.add_argument("--worker-role", default="codeadapt_worker")
    sub.add_parser(
        "db-fingerprint",
        help="schema revision, row counts and per-table SHA-256 as JSON (compare a source "
        "database with its restored copy)",
    )
    erase = sub.add_parser(
        "erase-learner",
        help="delete one account and every row derived from it (participant withdrawal); "
        "dry run unless --apply",
    )
    erase.add_argument("username")
    erase.add_argument("--apply", action="store_true")
    purge = sub.add_parser(
        "purge-sessions",
        help="delete login sessions that expired or were revoked long ago (dry run unless --apply)",
    )
    purge.add_argument("--older-than-days", type=float, default=30.0)
    purge.add_argument("--apply", action="store_true")
    setup = sub.add_parser(
        "db-setup",
        help="as the schema owner: create or update the API and worker login roles "
        "(passwords from CODEADAPT_API_DB_PASSWORD and CODEADAPT_WORKER_DB_PASSWORD) and "
        "apply the grants",
    )
    setup.add_argument("--api-role", default="codeadapt_api")
    setup.add_argument("--worker-role", default="codeadapt_worker")
    args = parser.parse_args(argv)
    if args.command == "db-grants":  # needs no database connection
        for statement in roles.grant_statements(args.api_role, args.worker_role):
            print(f"{statement};")
        return 0

    settings = Settings.from_env()
    if args.command == "db-setup":
        return _db_setup(settings.database_url, args.api_role, args.worker_role)
    if args.command == "backup":
        return _backup(settings.database_url, args.destination)
    sessions = make_session_factory(make_engine(settings.database_url))
    with sessions() as session:
        if args.command == "status":
            return _status(session, args)
        if args.command == "erase-learner":
            target = auth.find_user(session, args.username)
            if target is None:
                raise SystemExit(f"no user {args.username!r}")
            try:
                counts = ops.erase_learner(session, target.id, args.apply)
            except ProgrammingError as exc:
                if "permission denied" not in str(exc):
                    raise
                # R7: the API role cannot change or delete audit rows.
                raise SystemExit(
                    "erase-learner must run as the schema owner: use the `admin` Compose "
                    "service (production runbook §4b), not the API container"
                ) from None
            if args.apply:
                # A record that an erasure happened, without the erased name.
                auth.audit(
                    session,
                    auth.AuditKind.ACCOUNT_ERASED,
                    username="(erased)",
                    client=_OPERATOR,
                    target=f"rows={sum(counts.values())}",
                )
                session.commit()
            print(json.dumps({"applied": args.apply, "rows": counts}))
            return 0
        if args.command == "purge-sessions":
            n = ops.purge_dead_sessions(session, utcnow(), args.older_than_days, args.apply)
            done = "deleted" if args.apply else "found (dry run)"
            print(f"purge-sessions: {n} dead session(s) {done}")
            return 0
        if args.command == "db-fingerprint":
            print(json.dumps(ops.database_fingerprint(session), sort_keys=True))
            return 0
        if args.command == "list":
            for u in session.scalars(select(User).order_by(User.username)):
                login = "disabled" if u.disabled else ("login" if u.password_hash else "no-login")
                print(f"{u.username}\t{u.role}\t{u.data_class}\t{login}")
            return 0
        user = auth.find_user(session, args.username)
        if args.command == "create-user":
            if user is not None:
                # Names ignore case (ADR-041); the unique index on lower(username) also
                # refuses a concurrent duplicate at commit.
                raise SystemExit(f"user {user.username!r} already exists (names ignore case)")
            if args.role in STAFF_ROLES and not args.allow_second_staff:
                existing = _staff_logins(session)
                if existing:
                    # One researcher login sees everything (ADR-045); a second one is an
                    # explicit choice, not a typo in --role.
                    names = ", ".join(u.username for u in existing)
                    raise SystemExit(
                        f"a researcher/admin login already exists ({names}); disable it "
                        "first or pass --allow-second-staff"
                    )
            user = User(
                username=args.username,
                role=args.role,
                data_class=args.data_class,
                password_hash=auth.hash_password(_read_password()),
            )
            session.add(user)
            session.flush()
            kind = auth.AuditKind.ACCOUNT_CREATED
        elif user is None:
            raise SystemExit(f"no user {args.username!r}")
        elif args.command == "set-password":
            user.password_hash = auth.hash_password(_read_password())
            user.disabled = False
            auth.revoke_all(session, user)
            kind = auth.AuditKind.PASSWORD_SET
        else:
            user.disabled = True
            auth.revoke_all(session, user)
            kind = auth.AuditKind.ACCOUNT_DISABLED
        auth.audit(session, kind, username=user.username, user=user, client=_OPERATOR)
        session.commit()
    print(f"{args.command}: {args.username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
