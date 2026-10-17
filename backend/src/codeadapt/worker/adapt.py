"""Run the adaptive policy after a diagnosis and persist its output (methodology §5).

The policy and the follow-up evaluation are pure; this module only turns stored rows into
their inputs and their outputs into rows.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from codeadapt.adaptation import (
    AttemptRecord,
    PolicyV1,
    Recommendation,
    SuccessCriterion,
    TestStatus,
    evaluate_followup,
)
from codeadapt.adaptation.models import Action, Rule
from codeadapt.adaptation.skillmap import SkillMap
from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import (
    DiagnosisRow,
    FollowupEvaluationRow,
    ProblemVersion,
    RecommendationRow,
    Submission,
)
from codeadapt.db.session import as_utc
from codeadapt.diagnosis import Outcome

# Attempts that produced no test evidence neither consume nor replace an open
# recommendation for the same problem: the learner is still working on it.
_NO_EVIDENCE = {Outcome.COMPILE_ERROR, Outcome.EXECUTION_ERROR}


def attempt_record(submission: Submission, slug: str, diagnosis: DiagnosisRow) -> AttemptRecord:
    """Rebuild per-test pass/fail/excluded from the diagnosis rationale's test table."""
    tests: dict[str, TestStatus] = {}
    for row in diagnosis.rationale.get("tests", []):
        if not row["reliable"]:
            tests[row["test"]] = TestStatus.EXCLUDED
        elif row["observed"] == row["reference"]:
            tests[row["test"]] = TestStatus.PASSED
        else:
            tests[row["test"]] = TestStatus.FAILED
    return AttemptRecord(
        submission_id=submission.id,
        problem_slug=slug,
        problem_version=submission.problem_version,
        created_at=as_utc(submission.created_at),
        outcome=Outcome(diagnosis.outcome),
        selected_model=diagnosis.selected_model,
        candidates=tuple(diagnosis.candidates),
        qualified=diagnosis.rationale.get("evidence_strength") == "single_behaviour",
        tests=tests,
    )


def learner_attempts(
    session: Session, user_id: int, data_class: str | None = None
) -> dict[str, AttemptRecord]:
    """Every diagnosed submission by the learner, using its latest diagnosis."""
    query = (
        select(Submission, DiagnosisRow, ProblemVersion.slug)
        .join(DiagnosisRow, DiagnosisRow.submission_id == Submission.id)
        .join(ProblemVersion, ProblemVersion.version == Submission.problem_version)
        .where(Submission.user_id == user_id)
    )
    if data_class is not None:
        query = query.where(Submission.data_class == data_class)
    rows = session.execute(query.order_by(Submission.created_at, DiagnosisRow.id))
    return {sub.id: attempt_record(sub, slug, diag) for sub, diag, slug in rows}


def skill_maps_for(session: Session, attempts: Iterable[AttemptRecord]) -> dict[str, SkillMap]:
    """The stored skill-map snapshot of every content version the attempts were made on."""
    versions = {a.problem_version for a in attempts if a.problem_version is not None}
    rows = session.scalars(select(ProblemVersion).where(ProblemVersion.version.in_(versions)))
    maps = {row.version: SkillMap.from_stored(row.skill_map) for row in rows}
    return {version: smap for version, smap in maps.items() if smap is not None}


def open_recommendation(session: Session, user_id: int) -> RecommendationRow | None:
    latest = session.scalar(
        select(RecommendationRow)
        .where(RecommendationRow.user_id == user_id)
        .order_by(RecommendationRow.id.desc())
        .limit(1)
    )
    if latest is None:
        return None
    evaluated = session.scalar(
        select(FollowupEvaluationRow.id).where(FollowupEvaluationRow.recommendation_id == latest.id)
    )
    return None if evaluated is not None else latest


def recommendation_of(row: RecommendationRow) -> Recommendation:
    return Recommendation(
        policy=row.policy,
        policy_version=row.policy_version,
        rule=Rule(row.rule),
        action=Action(row.action),
        problem_slug=row.problem_slug,
        target_skills=tuple(row.target_skills),
        criterion=SuccessCriterion.model_validate(row.criterion) if row.criterion else None,
        review_flag=row.review_flag,
        rationale=row.rationale,
    )


def adapt(
    session: Session,
    submission: Submission,
    diagnosis: DiagnosisRow,
    catalogue: Catalogue,
    policy: PolicyV1,
) -> tuple[RecommendationRow | None, FollowupEvaluationRow | None]:
    """Evaluate the learner's open recommendation if this attempt follows it, then recommend.

    Adds rows to the session without committing.
    """
    problems = {p.spec.slug: p.spec for p in catalogue.problems}
    attempts = learner_attempts(session, submission.user_id)
    index = attempts.get(submission.id)
    if index is None or index.problem_slug not in problems:
        return None, None

    pending = open_recommendation(session, submission.user_id)
    follows = (
        pending is not None
        and pending.problem_slug == index.problem_slug
        and pending.submission_id != submission.id
        and as_utc(submission.created_at) >= as_utc(pending.created_at)
    )
    evaluation: FollowupEvaluationRow | None = None
    if pending is not None and follows and index.outcome not in _NO_EVIDENCE:
        base = attempts.get(pending.submission_id)
        if base is not None:
            result = evaluate_followup(
                recommendation_of(pending),
                base,
                problems.get(base.problem_slug),
                index,
                problems[index.problem_slug],
            )
            evaluation = FollowupEvaluationRow(
                recommendation_id=pending.id,
                submission_id=submission.id,
                diagnosis_id=diagnosis.id,
                method=result.method,
                method_version=result.method_version,
                verdict=result.verdict.value,
                reason=result.reason,
                passed=result.passed,
                failed=result.failed,
                excluded=result.excluded,
                probes=[p.model_dump(mode="json") for p in result.probes],
                relation=result.relation.value,
            )
            session.add(evaluation)
    elif follows and index.outcome in _NO_EVIDENCE:
        return None, None  # keep the open recommendation; nothing new was learned

    history = list(attempts.values())
    rec = policy.recommend(index, history, problems, skill_maps_for(session, history))
    row = RecommendationRow(
        user_id=submission.user_id,
        submission_id=submission.id,
        diagnosis_id=diagnosis.id,
        policy=rec.policy,
        policy_version=rec.policy_version,
        rule=rec.rule.value,
        action=rec.action.value,
        problem_slug=rec.problem_slug,
        target_skills=list(rec.target_skills),
        criterion=rec.criterion.model_dump(mode="json") if rec.criterion else None,
        review_flag=rec.review_flag,
        rationale=rec.rationale,
    )
    session.add(row)
    return row, evaluation
