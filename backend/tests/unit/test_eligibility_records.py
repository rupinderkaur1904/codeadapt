"""Stored records under D1 (ADR-035) and the L22 taxonomy migration (ADR-034), through the API.

A banned-name attempt keeps its submission, run and diagnosis and still counts in attempt
statistics; only its skill observations are withheld. An attempt made on a version whose
snapshot predates the change keeps the evidence and the skill keys it had; retired keys are
shown to researchers as deprecated, with their historical definition, never converted.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from codeadapt.adaptation import SkillMap
from codeadapt.api.app import create_app
from codeadapt.config import Settings
from codeadapt.content.catalogue import Catalogue
from codeadapt.content.taxonomy import RETIRED
from codeadapt.db.models import (
    DataClass,
    DiagnosisRow,
    Environment,
    ExecutionRun,
    Job,
    JobState,
    ProblemVersion,
    Submission,
    User,
    utcnow,
)
from tests.paths import DEMO_CONTENT

CATALOGUE = Catalogue.load(DEMO_CONTENT)
RESEARCHER = {"X-Dev-Role": "researcher"}
USES_LIBRARY = (
    "#include <algorithm>\n#include <vector>\n"
    "int lower_bound_index(const std::vector<int>& a, int t) {\n"
    "    return std::lower_bound(a.begin(), a.end(), t) - a.begin();\n}\n"
)
HAND_WRITTEN = "int lower_bound_index(const std::vector<int>& a, int t) { /* loop */ return 0; }"


@pytest.fixture
def client(settings: Settings, sessions: sessionmaker[Session]) -> TestClient:
    return TestClient(create_app(settings, sessions, CATALOGUE))


def record(
    sessions: sessionmaker[Session], user_id: int, version: str, slug: str, source: str, n: int
) -> str:
    """A stored, diagnosed no-failure attempt on `version` (no execution needed)."""
    tests = (CATALOGUE.by_slug[slug].spec.tests) if slug in CATALOGUE.by_slug else ()
    with sessions() as s:
        sub = Submission(
            user_id=user_id,
            problem_version=version,
            source=source,
            source_sha256="0" * 64,
            origin="synthetic",
            data_class=DataClass.DEV.value,
            created_at=utcnow() + timedelta(seconds=n),
        )
        s.add(sub)
        s.flush()
        s.add(Job(submission_id=sub.id, state=JobState.DONE.value, attempts=1))
        env = s.scalar(select(Environment)) or Environment(digest="e" * 64, info={})
        s.add(env)
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
            compile_wall_ms=0,
            started_at=now,
            finished_at=now,
        )
        s.add(run)
        s.flush()
        rows = [
            {"test": t.key, "observed": "ok", "reference": "ok", "reliable": True} for t in tests
        ]
        s.add(
            DiagnosisRow(
                submission_id=sub.id,
                run_id=run.id,
                method="fingerprint_consistency",
                method_version="1",
                outcome="no_failure_observed",
                selected_model=None,
                candidates=[],
                support=0,
                rationale={"tests": rows},
            )
        )
        s.commit()
        return sub.id


def learner(sessions: sessionmaker[Session]) -> int:
    with sessions() as s:
        CATALOGUE.sync(s)
        user = User(username="dev-student", role="student", data_class=DataClass.DEV.value)
        s.add(user)
        s.commit()
        return user.id


def test_a_banned_call_withholds_skill_evidence_but_keeps_every_record(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    uid = learner(sessions)
    lb = CATALOGUE.by_slug["lower-bound"]
    banned = record(sessions, uid, lb.version, "lower-bound", USES_LIBRARY, 1)
    cot = CATALOGUE.by_slug["count-occurrences"]
    clean = record(sessions, uid, cot.version, "count-occurrences", HAND_WRITTEN, 2)

    trace = client.get(f"/api/v1/research/submissions/{banned}/trace", headers=RESEARCHER).json()
    assert trace["technique_check"]["found"] == ["std::lower_bound"]
    assert trace["technique_check"]["skill_evidence"] == "withheld"
    assert "does not show which algorithm" in trace["technique_check"]["note"]
    assert trace["diagnosis"] and trace["execution_runs"]  # run and diagnosis are kept
    assert trace["submission"]["source"] == USES_LIBRARY
    ok = client.get(f"/api/v1/research/submissions/{clean}/trace", headers=RESEARCHER).json()
    assert ok["technique_check"]["found"] == [] and ok["technique_check"]["skill_evidence"] == (
        "eligible"
    )

    body = client.get(
        "/api/v1/research/learner-model?username=dev-student", headers=RESEARCHER
    ).json()
    assert body["attempts"] == 2  # the banned attempt still counts as an attempt
    observed = {
        o["observation"]["submission_id"]
        for s in body["estimate"]["skills"]
        for o in s["observations"]
    }
    assert observed == {clean}
    metrics = client.get("/api/v1/research/metrics", headers=RESEARCHER).json()
    assert metrics["submissions"] == 2
    assert metrics["outcomes"] == {"no_failure_observed": 2}


def test_a_problem_without_bans_has_no_technique_check(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    uid = learner(sessions)
    sp = CATALOGUE.by_slug["stock-profit"]
    sub = record(sessions, uid, sp.version, "stock-profit", "std::lower_bound(b, e, t);", 1)
    trace = client.get(f"/api/v1/research/submissions/{sub}/trace", headers=RESEARCHER).json()
    assert trace["technique_check"] is None


def test_an_older_snapshot_keeps_its_evidence_and_its_retired_skill_keys(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    uid = learner(sessions)
    lb = CATALOGUE.by_slug["lower-bound"]
    current = SkillMap.from_spec(lb.spec, "lb-pre-2026-10-26")
    # A snapshot as stored before 2026-10-26: no banned_names field at all.
    old_lb = current.model_dump(mode="json")
    del old_lb["banned_names"]
    # stock-profit as it was declared under ADR-033, with the now-retired `index_range`.
    sp = SkillMap.from_spec(CATALOGUE.by_slug["stock-profit"].spec, "sp-pre-2026-10-26")
    rename = {"loop_bounds": "index_range"}
    old_sp = sp.model_copy(
        update={
            "test_skills": {
                k: tuple(sorted(rename.get(s, s) for s in v)) for k, v in sp.test_skills.items()
            },
            "model_skills": {k: rename.get(v, v) for k, v in sp.model_skills.items()},
        }
    ).model_dump(mode="json")
    with sessions() as s:
        for version, slug, snap in (
            ("lb-pre-2026-10-26", "lower-bound", old_lb),
            ("sp-pre-2026-10-26", "stock-profit", old_sp),
        ):
            s.add(ProblemVersion(version=version, slug=slug, family="x", title="x", skill_map=snap))
        s.commit()
    banned = record(sessions, uid, "lb-pre-2026-10-26", "lower-bound", USES_LIBRARY, 1)
    record(sessions, uid, "sp-pre-2026-10-26", "stock-profit", HAND_WRITTEN, 2)

    trace = client.get(f"/api/v1/research/submissions/{banned}/trace", headers=RESEARCHER).json()
    assert trace["technique_check"] is None  # that version declared no bans
    body = client.get(
        "/api/v1/research/learner-model?username=dev-student", headers=RESEARCHER
    ).json()
    skills = {s["skill"] for s in body["estimate"]["skills"]}
    # The pre-change attempt kept its evidence; the old key was not converted.
    assert "search_space_boundaries" in skills
    assert "index_range" in skills and "loop_bounds" not in skills
    assert set(body["retired_skills"]) == {"index_range"}
    retired = body["retired_skills"]["index_range"]
    assert retired["definition"] == RETIRED["index_range"].definition
    assert retired["replaced_by"] == ["loop_bounds", "range_inclusion"]
    assert retired["decision"] == "ADR-034"
