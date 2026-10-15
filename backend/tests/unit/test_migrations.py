from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from codeadapt.db.models import Base
from codeadapt.db.session import make_engine


def test_migrations_match_models(db_url: str) -> None:
    engine = make_engine(db_url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    engine.dispose()
    assert diff == []
