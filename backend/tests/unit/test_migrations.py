from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from codeadapt.db.migrate import alembic_config
from codeadapt.db.models import Base
from codeadapt.db.session import make_engine
from tests.unit.test_auth_parity import blank_db_url  # noqa: F401 - fixture


def test_migrations_match_models(db_url: str) -> None:
    engine = make_engine(db_url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    engine.dispose()
    assert diff == []


# ---------------------------------------------------------------- M3.5 migration safety


def test_every_revision_upgrades_and_downgrades_step_by_step(blank_db_url: str) -> None:  # noqa: F811 - fixture
    """On a blank disposable database: up one revision at a time to head, down one at a
    time to base, and up to head again; the final schema matches the models."""
    cfg = alembic_config(blank_db_url)
    revisions = [
        r.revision for r in reversed(list(ScriptDirectory.from_config(cfg).walk_revisions()))
    ]
    assert revisions[:1] == ["0001"] and revisions[-1] == "0006"
    for rev in revisions:
        command.upgrade(cfg, rev)
    for rev in reversed(revisions[:-1]):
        command.downgrade(cfg, rev)
    command.downgrade(cfg, "base")
    engine = make_engine(blank_db_url)
    with engine.connect() as conn:
        assert set(inspect(conn).get_table_names()) <= {"alembic_version"}
    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    engine.dispose()
    assert diff == []
