from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import Session, sessionmaker

from codeadapt.config import Environment, Settings
from codeadapt.db.migrate import upgrade
from codeadapt.db.session import make_engine, make_session_factory
from tests.paths import DEMO_CONTENT

# Set to a PostgreSQL server URL (e.g. postgresql+psycopg://postgres:pw@localhost/postgres)
# to run every database test against a fresh PostgreSQL database instead of SQLite.
POSTGRES_URL = os.environ.get("CODEADAPT_TEST_POSTGRES_URL")


@pytest.fixture
def db_url(tmp_path: Path) -> Iterator[str]:
    if not POSTGRES_URL:
        url = f"sqlite:///{tmp_path / 'test.sqlite3'}"
        upgrade(url)
        yield url
        return
    name = f"codeadapt_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(POSTGRES_URL).set(database=name).render_as_string(hide_password=False)
    upgrade(url)
    yield url
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture
def sessions(db_url: str) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(db_url)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def settings(db_url: str) -> Settings:
    return Settings(env=Environment.TEST, database_url=db_url, content_dir=DEMO_CONTENT)
