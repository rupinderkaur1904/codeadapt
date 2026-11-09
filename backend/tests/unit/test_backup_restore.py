"""M3.5: a PostgreSQL dump made by deploy/backup/pg-backup.sh restores, with
deploy/backup/pg-restore.sh, into a new database whose every row matches the source.

This is an actual restore on disposable databases, not just a successful dump. PostgreSQL
only (CODEADAPT_TEST_POSTGRES_URL) and needs pg_dump/pg_restore/psql/createdb on PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import Session, sessionmaker

from codeadapt import auth, ops
from codeadapt.db.session import make_engine, make_session_factory
from codeadapt.diagnosis import FingerprintConsistencyV1
from tests.conftest import POSTGRES_URL
from tests.unit.test_pipeline_redelivery import record_diagnosis
from tests.unit.test_queue import enqueue

REPO = Path(__file__).resolve().parents[3]
BACKUP = REPO / "deploy" / "backup" / "pg-backup.sh"
RESTORE = REPO / "deploy" / "backup" / "pg-restore.sh"

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL or not all(shutil.which(t) for t in ("pg_dump", "pg_restore", "psql")),
    reason="needs CODEADAPT_TEST_POSTGRES_URL and PostgreSQL client tools",
)


def _libpq_env(url: str) -> dict[str, str]:
    u = make_url(url)
    return {
        **os.environ,
        "PGHOST": u.host or "localhost",
        "PGPORT": str(u.port or 5432),
        "PGUSER": u.username or "",
        "PGPASSWORD": u.password or "",
        "PGDATABASE": u.database or "",
    }


def _populate(sessions: sessionmaker[Session]) -> None:
    ids = enqueue(sessions, 3)
    record_diagnosis(sessions, ids[0], FingerprintConsistencyV1())
    with sessions() as s:
        user = auth.find_user(s, "u")
        assert user is not None
        user.password_hash = auth.hash_password("correct horse battery")
        auth.start_session(s, user, timedelta(hours=1))
        auth.audit(s, auth.AuditKind.LOGIN, username="u", user=user, client="t")
        s.commit()


def _fingerprint(url: str) -> dict[str, object]:
    engine = make_engine(url)
    with make_session_factory(engine)() as s:
        result = ops.database_fingerprint(s)
    engine.dispose()
    return result


def test_backup_restores_every_row_into_a_new_database(
    db_url: str, sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    _populate(sessions)
    env = _libpq_env(db_url)
    out = subprocess.run(
        [str(BACKUP)],
        env={**env, "BACKUP_DIR": str(tmp_path)},
        check=True,
        capture_output=True,
        text=True,
    )
    (dump,) = tmp_path.glob("codeadapt-*.dump")
    assert dump.with_name(dump.name + ".sha256").exists()
    assert (dump.stat().st_mode & 0o777) == 0o600  # learner data: owner-only
    assert "backup:" in out.stdout

    target = f"codeadapt_restore_{uuid.uuid4().hex[:10]}"
    restored_url = make_url(db_url).set(database=target).render_as_string(hide_password=False)
    admin = create_engine(POSTGRES_URL or "", isolation_level="AUTOCOMMIT")
    try:
        r = subprocess.run(
            [str(RESTORE), str(dump), target], env=env, capture_output=True, text=True
        )
        assert r.returncode == 0, r.stderr
        assert "checksum ok" in r.stdout
        source, copy = _fingerprint(db_url), _fingerprint(restored_url)
        assert copy == source
        tables = source["tables"]
        assert isinstance(tables, dict)
        for name in ("users", "submissions", "jobs", "diagnoses", "auth_sessions"):
            assert tables[name]["rows"] > 0, name  # the comparison covered real data
        assert source["schema_revision"] == "0007"

        # Restoring over an existing database is refused, and leaves it untouched.
        again = subprocess.run(
            [str(RESTORE), str(dump), target], env=env, capture_output=True, text=True
        )
        assert again.returncode == 3
        assert _fingerprint(restored_url) == source
    finally:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{target}" WITH (FORCE)'))
        admin.dispose()


def test_restore_refuses_a_corrupted_dump(
    db_url: str, sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    _populate(sessions)
    env = _libpq_env(db_url)
    subprocess.run([str(BACKUP)], env={**env, "BACKUP_DIR": str(tmp_path)}, check=True)
    (dump,) = tmp_path.glob("codeadapt-*.dump")
    with dump.open("r+b") as f:
        f.seek(100)
        f.write(b"\x00corrupt\x00")
    target = f"codeadapt_restore_{uuid.uuid4().hex[:10]}"
    r = subprocess.run([str(RESTORE), str(dump), target], env=env, capture_output=True)
    assert r.returncode != 0  # checksum mismatch: nothing is created
    admin = create_engine(POSTGRES_URL or "", isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :d"), {"d": target}
        ).scalar()
    admin.dispose()
    assert exists is None


def test_restore_rejects_unsafe_database_names(db_url: str, tmp_path: Path) -> None:
    dump = tmp_path / "x.dump"
    dump.write_bytes(b"")
    r = subprocess.run(
        [str(RESTORE), str(dump), 'x"; DROP DATABASE postgres; --'],
        env=_libpq_env(db_url),
        capture_output=True,
    )
    assert r.returncode == 2
