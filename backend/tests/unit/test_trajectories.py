"""Scripted synthetic learner trajectories through the worker's adaptation step (M6).

Each learner is a `synthetic` user whose diagnosed attempts are written straight to the
database, so the sequence of recommendations and follow-up verdicts is checked end to end
without the sandbox. These are acceptance tests of the policy's mechanics; they say
nothing about whether the policy helps real students learn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from codeadapt.adaptation import PolicyV1
from codeadapt.api.app import create_app
from codeadapt.config import Settings
from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import (
    DataClass,
    DiagnosisRow,
    Environment,
    ExecutionRun,
    FollowupEvaluationRow,
    RecommendationRow,
    Submission,
    User,
    utcnow,
)
from codeadapt.diagnosis import Outcome
from codeadapt.worker.adapt import adapt, open_recommendation
from tests.paths import DEMO_CONTENT

CATALOGUE = Catalogue.load(DEMO_CONTENT)

Step = tuple[str, str, str | None, str | None]  # (rule, action, problem, verdict)


@dataclass
class Learner:
    sessions: sessionmaker[Session]
    user_id: int
    clock: int = 0
    steps: list[Step] = field(default_factory=list)

    @classmethod
    def create(cls, sessions: sessionmaker[Session], name: str, **kw: str) -> Learner:
        with sessions() as s:
            CATALOGUE.sync(s)
            user = s.scalar(select(User).where(User.username == name))
            if user is None:
                user = User(
                    username=name,
                    role="student",
                    data_class=kw.get("data_class", DataClass.SYNTHETIC.value),
                )
                s.add(user)
                s.commit()
            return cls(sessions, user.id)

    def submit(
        self,
        slug: str,
        outcome: Outcome,
        *,
        model: str | None = None,
        failing: tuple[str, ...] = (),
        excluded: tuple[str, ...] = (),
        created_offset: timedelta | None = None,
    ) -> Step | None:
        """Record one diagnosed attempt and run the adaptation step on it."""
        self.clock += 1
        problem = CATALOGUE.by_slug[slug]
        with self.sessions() as s:
            sub = Submission(
                user_id=self.user_id,
                problem_version=problem.version,
                source="// synthetic",
                source_sha256="0" * 64,
                origin="synthetic",
                data_class=DataClass.SYNTHETIC.value,
                created_at=utcnow() + (created_offset or timedelta(seconds=self.clock)),
            )
            s.add(sub)
            env = s.scalar(select(Environment)) or Environment(digest="0" * 64, info={})
            s.add(env)
            s.flush()
            now = utcnow()
            run = ExecutionRun(
                submission_id=sub.id,
                environment_id=env.id,
                profile="standard",
                compile_status="ok" if outcome is not Outcome.COMPILE_ERROR else "error",
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
            rows = []
            if outcome not in (Outcome.COMPILE_ERROR, Outcome.EXECUTION_ERROR):
                for t in problem.spec.tests:
                    rows.append(
                        {
                            "test": t.key,
                            "observed": "output:wrong" if t.key in failing else "output:ok",
                            "reference": "output:ok",
                            "reliable": t.key not in excluded,
                        }
                    )
            diagnosis = DiagnosisRow(
                submission_id=sub.id,
                run_id=run.id,
                method="fingerprint_consistency",
                method_version="1",
                outcome=outcome.value,
                selected_model=model,
                candidates=[model] if model else [],
                support=len(failing),
                rationale={"tests": rows},
            )
            s.add(diagnosis)
            s.flush()
            rec, ev = adapt(s, sub, diagnosis, CATALOGUE, PolicyV1())
            s.commit()
            if rec is None:
                return None
            step = (rec.rule, rec.action, rec.problem_slug, ev.verdict if ev else None)
            self.steps.append(step)
            return step


def test_targeted_practice_then_progression_through_the_family(
    sessions: sessionmaker[Session],
) -> None:
    a = Learner.create(sessions, "synthetic-a")
    a.submit(
        "lower-bound",
        Outcome.HYPOTHESIS_SUPPORTED,
        model="upper_bound_confusion",
        failing=("sample_present", "equal_first", "equal_last"),
    )
    a.submit("count-occurrences", Outcome.NO_FAILURE_OBSERVED)
    a.submit("last-less-than", Outcome.NO_FAILURE_OBSERVED)
    a.submit("lower-bound", Outcome.NO_FAILURE_OBSERVED)
    assert a.steps == [
        ("hypothesis_supported", "new_problem", "count-occurrences", None),
        ("no_failure_observed", "new_problem", "last-less-than", "criterion_met"),
        ("no_failure_observed", "new_problem", "lower-bound", "criterion_met"),
        ("no_failure_observed", "none", None, "criterion_met"),
    ]


def test_persistent_error_is_not_reported_as_improvement(
    sessions: sessionmaker[Session],
) -> None:
    b = Learner.create(sessions, "synthetic-b")
    b.submit(
        "lower-bound",
        Outcome.HYPOTHESIS_SUPPORTED,
        model="upper_bound_confusion",
        failing=("sample_present", "equal_first"),
    )
    b.submit(
        "count-occurrences",
        Outcome.HYPOTHESIS_SUPPORTED,
        model="upper_uses_strict",
        failing=("sample_run", "unique_middle", "run_at_start", "all_equal"),
    )
    b.submit(
        "last-less-than",
        Outcome.HYPOTHESIS_SUPPORTED,
        model="uses_le",
        failing=("sample_present", "equal_first"),
    )
    assert b.steps == [
        ("hypothesis_supported", "new_problem", "count-occurrences", None),
        ("hypothesis_supported", "new_problem", "last-less-than", "criterion_not_met"),
        # Everything is recent now, so the densest equality problem comes back.
        ("hypothesis_supported", "new_problem", "count-occurrences", "criterion_not_met"),
    ]


def test_compile_errors_keep_the_open_recommendation(sessions: sessionmaker[Session]) -> None:
    c = Learner.create(sessions, "synthetic-c")
    c.submit(
        "lower-bound",
        Outcome.HYPOTHESIS_SUPPORTED,
        model="hi_init_last_index",
        failing=("above_all", "single_above", "large_above_all"),
    )
    assert c.submit("count-occurrences", Outcome.COMPILE_ERROR) is None
    assert c.submit("count-occurrences", Outcome.EXECUTION_ERROR) is None
    step = c.submit("count-occurrences", Outcome.NO_FAILURE_OBSERVED)
    assert step is not None
    assert step[3] == "criterion_met"
    with sessions() as s:
        assert s.scalar(select(FollowupEvaluationRow.passed)) == 7  # search-space tests


def test_a_new_attempt_elsewhere_supersedes_without_a_verdict(
    sessions: sessionmaker[Session],
) -> None:
    d = Learner.create(sessions, "synthetic-d")
    d.submit(
        "lower-bound",
        Outcome.HYPOTHESIS_SUPPORTED,
        model="upper_bound_confusion",
        failing=("sample_present", "equal_first"),
    )
    d.submit("last-less-than", Outcome.NO_FAILURE_OBSERVED)
    assert [s[3] for s in d.steps] == [None, None]
    with sessions() as s:
        assert s.scalar(select(FollowupEvaluationRow)) is None
        latest = open_recommendation(s, d.user_id)
        assert latest is not None
        assert latest.rule == "no_failure_observed"


def test_abstention_then_retry_is_not_comparable(sessions: sessionmaker[Session]) -> None:
    e = Learner.create(sessions, "synthetic-e")
    e.submit("last-less-than", Outcome.UNMODELLED_BEHAVIOUR, failing=("empty", "below_all"))
    e.submit("last-less-than", Outcome.NO_FAILURE_OBSERVED)
    assert e.steps == [
        ("abstained", "retry", "last-less-than", None),
        ("no_failure_observed", "new_problem", "count-occurrences", "not_comparable"),
    ]
    with sessions() as s:
        first = s.scalars(select(RecommendationRow).order_by(RecommendationRow.id)).first()
        assert first is not None
        assert first.review_flag
        assert first.criterion is None


def test_attempt_created_before_the_recommendation_is_not_its_followup(
    sessions: sessionmaker[Session],
) -> None:
    f = Learner.create(sessions, "synthetic-f")
    f.submit(
        "lower-bound",
        Outcome.HYPOTHESIS_SUPPORTED,
        model="upper_bound_confusion",
        failing=("sample_present", "equal_first"),
    )
    # Submitted before that recommendation existed (e.g. queued behind it).
    f.submit("count-occurrences", Outcome.NO_FAILURE_OBSERVED, created_offset=timedelta(hours=-1))
    assert f.steps[-1][3] is None


# ---------------------------------------------------------------------- student API
@pytest.fixture
def client(settings: Settings, sessions: sessionmaker[Session]) -> TestClient:
    return TestClient(create_app(settings, sessions, CATALOGUE))


STUDENT = {"X-Dev-Role": "student"}


def test_me_recommendation_shows_next_problem_and_verdict_without_internal_labels(
    client: TestClient, sessions: sessionmaker[Session]
) -> None:
    empty = client.get("/api/v1/me/recommendation", headers=STUDENT).json()
    assert empty == {"recommendation": None, "last_followup": None}

    me = Learner.create(sessions, "dev-student")
    me.submit(
        "lower-bound",
        Outcome.HYPOTHESIS_SUPPORTED,
        model="upper_bound_confusion",
        failing=("sample_present", "equal_first"),
    )
    body = client.get("/api/v1/me/recommendation", headers=STUDENT).json()
    rec = body["recommendation"]
    assert rec["action"] == "new_problem"
    assert rec["problem_slug"] == "count-occurrences"
    assert rec["problem_title"] == "Count occurrences"
    assert rec["focus"] == [CATALOGUE.by_slug["count-occurrences"].spec.skills["equality_handling"]]
    assert body["last_followup"] is None

    me.submit("count-occurrences", Outcome.NO_FAILURE_OBSERVED)
    body = client.get("/api/v1/me/recommendation", headers=STUDENT).json()
    assert body["last_followup"]["verdict"] == "criterion_met"
    assert "passed all 9 tests" in body["last_followup"]["message"]
    text = str(body).lower()
    for internal in ("upper_bound_confusion", "equality_handling", "rule_policy", "mastered"):
        assert internal not in text

    # Another learner's state is not visible.
    other = client.get("/api/v1/me/recommendation", headers={"X-Dev-Role": "researcher"}).json()
    assert other == {"recommendation": None, "last_followup": None}
