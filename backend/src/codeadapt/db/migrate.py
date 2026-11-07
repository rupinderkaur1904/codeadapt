"""Apply Alembic migrations programmatically (tests, local setup)."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection

_BACKEND = Path(__file__).resolve().parents[3]


def alembic_config(database_url: str) -> Config:
    cfg = Config(str(_BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND / "migrations"))
    cfg.attributes["database_url"] = database_url
    cfg.attributes["configure_logger"] = False
    return cfg


def upgrade(database_url: str) -> None:
    command.upgrade(alembic_config(database_url), "head")


def head_revision() -> str | None:
    """The newest migration this code ships (what `alembic upgrade head` would reach)."""
    return ScriptDirectory.from_config(alembic_config("")).get_current_head()


def current_revision(connection: Connection) -> str | None:
    """The revision the database is at; None if it was never migrated."""
    return MigrationContext.configure(connection).get_current_revision()
