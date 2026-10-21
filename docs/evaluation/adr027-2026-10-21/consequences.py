"""What one diagnosis leads to downstream, computed with the production code.

For a single attempt (no history): the skill observations ledger policy 1.2 would add, the
recommendation policy 1.3 (for v1.1 diagnoses) or 1.4 (for v1.2 diagnoses) would make,
and the feedback kind and whether a hint is shown. Used by replay_val1a.py and
compare_sets.py. Changes no production code.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from codeadapt.adaptation import AttemptRecord, PolicyV1, TestStatus, skill_observations
from codeadapt.api.feedback import feedback_view
from codeadapt.content.catalogue import LoadedProblem
from codeadapt.content.models import ProblemSpec
from codeadapt.db.models import DiagnosisRow
from codeadapt.diagnosis import Diagnosis
from codeadapt.evidence import OutcomeKind, Signature

T0 = datetime(2026, 1, 1, tzinfo=UTC)
POLICY_V1_4 = PolicyV1()


def parse_signature(text: str) -> Signature:
    kind, _, detail = text.partition(":")
    return Signature(kind=OutcomeKind(kind), detail=detail)


def attempt_from(diagnosis: Diagnosis, slug: str) -> AttemptRecord:
    """As worker/adapt.py::attempt_record rebuilds it from a stored diagnosis."""
    tests: dict[str, TestStatus] = {}
    for row in diagnosis.rationale.get("tests", []):
        if not row["reliable"]:
            tests[row["test"]] = TestStatus.EXCLUDED
        elif row["observed"] == row["reference"]:
            tests[row["test"]] = TestStatus.PASSED
        else:
            tests[row["test"]] = TestStatus.FAILED
    return AttemptRecord(
        submission_id="replay",
        problem_slug=slug,
        created_at=T0,
        outcome=diagnosis.outcome,
        selected_model=diagnosis.selected_model,
        candidates=tuple(diagnosis.candidates),
        qualified=diagnosis.rationale.get("evidence_strength") == "single_behaviour",
        tests=tests,
    )


def policy_for(version: str) -> PolicyV1:
    # Policy 1.3 and 1.4 differ only in the rule for the new outcome, which v1.1 never
    # produces, so 1.4 gives 1.3's recommendation for every v1.1 diagnosis
    # (tests/unit/test_adaptation.py golden-file test).
    return POLICY_V1_4 if version == "1.2" else PolicyV1(version="1.3")


def consequences(
    diagnosis: Diagnosis,
    problem: LoadedProblem,
    problems: dict[str, ProblemSpec],
) -> dict[str, Any]:
    slug = problem.spec.slug
    a = attempt_from(diagnosis, slug)
    obs = skill_observations([a], problems)
    out: dict[str, Any] = {
        "outcome": diagnosis.outcome.value,
        "selected_model": diagnosis.selected_model,
        "evidence_strength": diagnosis.rationale.get("evidence_strength"),
        "known_limitation": bool(
            diagnosis.selected_model
            and problem.error_model(diagnosis.selected_model).known_limitation
        ),
        "timed_out_tests": diagnosis.rationale.get("timed_out_tests", []),
        "consistent_models": diagnosis.rationale.get("consistent_models", []),
        "skill_observations": sorted(f"{o.skill}:{o.value}" for o in obs),
    }
    rec = policy_for(diagnosis.method_version).recommend(a, [a], problems)
    out["recommendation"] = {
        "policy_version": rec.policy_version,
        "rule": rec.rule.value,
        "action": rec.action.value,
        "problem": rec.problem_slug,
        "target_skills": list(rec.target_skills),
        "criterion": rec.criterion is not None,
        "review_flag": rec.review_flag,
    }
    row = DiagnosisRow(
        outcome=diagnosis.outcome.value,
        selected_model=diagnosis.selected_model,
        rationale=diagnosis.rationale,
    )
    view = feedback_view(problem, row, [])
    out["feedback"] = {"kind": view.kind.value, "hint_shown": view.hint is not None}
    return out
