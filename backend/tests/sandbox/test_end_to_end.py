"""M3 acceptance: API -> queue -> worker -> sandbox -> evidence -> diagnosis -> feedback.

These are synthetic submissions (ADR-008); they check the mechanism, not real-world accuracy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from codeadapt.api.app import create_app
from codeadapt.config import Settings
from codeadapt.content.catalogue import Catalogue
from codeadapt.db import queue
from codeadapt.diagnosis import FingerprintConsistencyV1
from codeadapt.execution import DockerSandbox
from codeadapt.worker.pipeline import Pipeline
from tests.paths import DEMO_CONTENT

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "lower_bound"
PROBLEM_DIR = DEMO_CONTENT / "lower-bound"
STUDENT = {"X-Dev-Role": "student"}
RESEARCHER = {"X-Dev-Role": "researcher"}


class Harness:
    def __init__(
        self, settings: Settings, sessions: sessionmaker[Session], sandbox: DockerSandbox
    ) -> None:
        self.catalogue = Catalogue.load(settings.content_dir)
        self.client = TestClient(create_app(settings, sessions, self.catalogue))
        self.sessions = sessions
        self.pipeline = Pipeline(sandbox, sessions, self.catalogue, FingerprintConsistencyV1())

    async def submit(self, source: str) -> tuple[dict[str, Any], dict[str, Any]]:
        r = self.client.post(
            "/api/v1/submissions",
            json={"problem_slug": "lower-bound", "source": source},
            headers=STUDENT,
        )
        assert r.status_code == 202, r.text
        sub_id = r.json()["id"]
        with self.sessions() as s:
            job = queue.claim_next(s, "test-worker", lease_seconds=600, max_attempts=3)
        assert job is not None
        await self.pipeline.handle(job)
        view = self.client.get(f"/api/v1/submissions/{sub_id}", headers=STUDENT).json()
        trace = self.client.get(
            f"/api/v1/research/submissions/{sub_id}/trace", headers=RESEARCHER
        ).json()
        return view, trace


@pytest.fixture
def harness(settings: Settings, sessions: sessionmaker[Session], sandbox: DockerSandbox) -> Harness:
    return Harness(settings, sessions, sandbox)


def assert_student_view_is_safe(view: dict[str, Any]) -> None:
    text = str(view)
    problem = Catalogue.load(DEMO_CONTENT).by_slug["lower-bound"]
    for model in problem.spec.error_models:
        assert model.key not in text
        assert model.description not in text
    for test in problem.spec.tests:
        if test.visibility.value == "hidden":
            # Values appear quoted in the repr; descriptions may legitimately contain words
            # like "empty", so compare whole values rather than substrings.
            assert f"'{test.key}'" not in text
            assert f"'{test.input}'" not in text


async def test_every_outcome_class_end_to_end(harness: Harness) -> None:
    # Sequential in one test so fingerprints are measured once and reused (cached in the DB).
    ref_view, ref_trace = await harness.submit((PROBLEM_DIR / "reference.cpp").read_text())
    assert ref_view["status"] == "completed"
    assert ref_trace["diagnosis"]["outcome"] == "no_failure_observed"
    assert ref_view["feedback"]["kind"] == "all_tests_passed"
    assert all(t["verdict"] == "passed" for t in ref_view["tests"])
    assert ref_trace["content_validation"]["errors"] == []
    assert ref_trace["environment"]["compiler_version"].startswith("g++")

    problem = harness.catalogue.by_slug["lower-bound"]
    for model in problem.spec.error_models:
        view, trace = await harness.submit((PROBLEM_DIR / model.file).read_text())
        diagnosis = trace["diagnosis"]
        assert diagnosis["outcome"] == "hypothesis_supported", (model.key, diagnosis)
        assert diagnosis["selected_model"] == model.key
        assert diagnosis["support"] >= 2
        assert view["feedback"]["kind"] == "recognised_pattern"
        assert view["feedback"]["hint"] == model.student_hint
        assert view["feedback"]["related_cases"]
        assert_student_view_is_safe(view)

    # A held-out variant written differently from the error model is still recognised.
    _, trace = await harness.submit((FIXTURES / "heldout_upper_bound_closed.cpp").read_text())
    assert trace["diagnosis"]["outcome"] == "hypothesis_supported"
    assert trace["diagnosis"]["selected_model"] == "upper_bound_confusion"

    # A different correct algorithm: no failure observed.
    _, trace = await harness.submit((FIXTURES / "heldout_correct_iterative.cpp").read_text())
    assert trace["diagnosis"]["outcome"] == "no_failure_observed"

    # Two bugs at once: outside the model space, so the method abstains.
    view, trace = await harness.submit((FIXTURES / "heldout_double_bug.cpp").read_text())
    assert trace["diagnosis"]["outcome"] == "unmodelled_behaviour"
    assert trace["diagnosis"]["selected_model"] is None
    assert view["feedback"]["kind"] == "failing_cases"
    assert view["feedback"]["hint"] is None
    assert_student_view_is_safe(view)

    # Compilation failure.
    view, trace = await harness.submit((FIXTURES / "compile_error.cpp").read_text())
    assert trace["diagnosis"]["outcome"] == "compile_error"
    assert view["compile"]["ok"] is False
    assert "expected ';'" in view["compile"]["diagnostics"]
    assert view["tests"] == []

    # Sample tests show input/expected/actual; hidden tests only their description.
    samples = [t for t in ref_view["tests"] if t["visibility"] == "sample"]
    hidden = [t for t in ref_view["tests"] if t["visibility"] == "hidden"]
    assert all(t["input"] and t["expected_output"] for t in samples)
    assert all(t["input"] is None and t["actual_output"] is None for t in hidden)


async def test_wrong_signature_is_a_compile_error_not_a_diagnosis(harness: Harness) -> None:
    view, trace = await harness.submit("int lower_bound_index(int x) { return x; }\n")
    assert trace["diagnosis"]["outcome"] == "compile_error"
    assert view["feedback"]["kind"] == "compile_error"
