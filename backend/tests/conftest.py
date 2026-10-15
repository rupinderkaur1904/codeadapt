from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from codeadapt.config import Environment, Settings
from codeadapt.db.migrate import upgrade
from codeadapt.db.session import make_engine, make_session_factory
from tests.paths import DEMO_CONTENT


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    url = f"sqlite:///{tmp_path / 'test.sqlite3'}"
    upgrade(url)
    return url


@pytest.fixture
def sessions(db_url: str) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(db_url)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def settings(db_url: str) -> Settings:
    return Settings(env=Environment.TEST, database_url=db_url, content_dir=DEMO_CONTENT)
