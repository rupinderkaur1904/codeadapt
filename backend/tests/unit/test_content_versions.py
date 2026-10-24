"""Content versions through the database (no Docker).

Editing a problem creates a new content-addressed version. Registration is append-only: the old
version keeps its row and its skill-map snapshot, and every attempt resolves the snapshot of the
version it was made on, never the current one.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from codeadapt.adaptation import SkillMap
from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import (
    DataClass,
    DiagnosisRow,
    Environment,
    ExecutionRun,
    ProblemVersion,
    Submission,
    User,
    utcnow,
)
from codeadapt.diagnosis import FingerprintConsistencyV1
from codeadapt.worker.adapt import learner_attempts, skill_maps_for
from tests.paths import DEMO_CONTENT

OLD_PROBE = 'two_elements = ["loop_termination"]'
NEW_PROBE = 'two_elements = ["loop_termination", "equality_handling"]'


def submit(sessions: sessionmaker[Session], user_id: int, version: str) -> None:
    """A submission on `version` with a recorded no-failure diagnosis (no execution needed)."""
    with sessions() as s:
        sub = Submission(
            user_id=user_id,
            problem_version=version,
            source="x",
            source_sha256="0" * 64,
            origin="student",
            data_class=DataClass.DEV.value,
        )
        env = s.scalar(select(Environment)) or Environment(digest="e" * 64, info={})
        s.add_all([sub, env])
        s.flush()
        now = utcnow()
        run = ExecutionRun(
            submission_id=sub.id,
            environment_id=env.id,
            profile="standard",
            compile_status="ok",
            compile_flags=[],
            compile_exit_code=0,
            compile_diagnostics="",
            compile_diagnostics_truncated=False,
            compile_wall_ms=1,
            started_at=now,
            finished_at=now,
        )
        s.add(run)
        s.flush()
        method = FingerprintConsistencyV1()
        s.add(
            DiagnosisRow(
                submission_id=sub.id,
                run_id=run.id,
                fingerprint_set_id=None,
                method=method.name,
                method_version=method.version,
                outcome="no_failure_observed",
                selected_model=None,
                candidates=[],
                support=0,
                rationale={},
            )
        )
        s.commit()


def test_an_edited_problem_gets_a_new_version_and_old_attempts_keep_their_snapshot(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    content = tmp_path / "content"
    shutil.copytree(DEMO_CONTENT, content)  # curriculum links need the whole bank
    old = Catalogue.load(content).by_slug["lower-bound"]
    with sessions() as s:
        Catalogue.load(content).sync(s)
        user = User(username="u", role="student", data_class=DataClass.DEV.value)
        s.add(user)
        s.commit()
        user_id = user.id
    submit(sessions, user_id, old.version)

    # Edit the skill mapping: a new version, registered next to the old one.
    toml = content / "lower-bound" / "problem.toml"
    text = toml.read_text()
    assert OLD_PROBE in text
    toml.write_text(text.replace(OLD_PROBE, NEW_PROBE, 1))
    new = Catalogue.load(content).by_slug["lower-bound"]
    assert new.version != old.version
    with sessions() as s:
        Catalogue.load(content).sync(s)
    submit(sessions, user_id, new.version)

    with sessions() as s:
        query = select(ProblemVersion).where(ProblemVersion.slug == "lower-bound")
        rows = {r.version: r for r in s.scalars(query)}
        assert set(rows) == {old.version, new.version}
        old_map = SkillMap.from_stored(rows[old.version].skill_map)
        new_map = SkillMap.from_stored(rows[new.version].skill_map)
        assert old_map == SkillMap.from_spec(old.spec, old.version)
        assert new_map == SkillMap.from_spec(new.spec, new.version)
        two = [t.key for t in old.spec.tests if "two_elements" in t.probes]
        changed = [k for k in two if "equality_handling" not in old_map.test_skills[k]]
        assert changed
        for key in changed:
            assert "equality_handling" in new_map.test_skills[key]

        attempts = list(learner_attempts(s, user_id, DataClass.DEV.value).values())
        assert {a.problem_version for a in attempts} == {old.version, new.version}
        assert len(attempts) == 2
        assert {a.problem_slug for a in attempts} == {"lower-bound"}
        maps = skill_maps_for(s, attempts)
        assert maps == {old.version: old_map, new.version: new_map}

    # Re-syncing either catalogue never rewrites a stored snapshot.
    with sessions() as s:
        Catalogue.load(DEMO_CONTENT).sync(s)
        Catalogue.load(content).sync(s)
        assert SkillMap.from_stored(s.get_one(ProblemVersion, old.version).skill_map) == old_map
