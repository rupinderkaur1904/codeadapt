"""Engine and session factory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def make_engine(url: str) -> Engine:
    kwargs: dict[str, Any] = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_connection: Any, _record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def as_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; every stored timestamp is UTC."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)
