"""`codeadapt-admin`: create accounts, set passwords, disable accounts (ADR-029); back up
a SQLite database.

Passwords are read from the terminal without echo, or from stdin when it is not a
terminal (one line). They are never accepted as command-line arguments, which other local
users could read from the process list.
"""

from __future__ import annotations

import argparse
import getpass
import sqlite3
import sys
from pathlib import Path

from sqlalchemy import select

from codeadapt import auth
from codeadapt.config import Settings
from codeadapt.db.models import DataClass, Role, User
from codeadapt.db.session import make_engine, make_session_factory

_OPERATOR = "codeadapt-admin"


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codeadapt-admin", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-user", help="create an account and set its password")
    create.add_argument("username")
    create.add_argument("--role", choices=[r.value for r in Role], required=True)
    create.add_argument("--data-class", choices=[d.value for d in DataClass], required=True)
    for name, text in (("set-password", "set a new password"), ("disable", "disable login")):
        p = sub.add_parser(name, help=f"{text}; ends the account's sessions")
        p.add_argument("username")
    sub.add_parser("list", help="list accounts")
    backup = sub.add_parser("backup", help="consistent online copy of a SQLite database")
    backup.add_argument("destination", type=Path)
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    if args.command == "backup":
        return _backup(settings.database_url, args.destination)
    sessions = make_session_factory(make_engine(settings.database_url))
    with sessions() as session:
        if args.command == "list":
            for u in session.scalars(select(User).order_by(User.username)):
                login = "disabled" if u.disabled else ("login" if u.password_hash else "no-login")
                print(f"{u.username}\t{u.role}\t{u.data_class}\t{login}")
            return 0
        user = session.scalar(select(User).where(User.username == args.username))
        if args.command == "create-user":
            if user is not None:
                raise SystemExit(f"user {args.username!r} already exists")
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
