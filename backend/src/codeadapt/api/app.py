"""FastAPI application. This process never talks to Docker (security.md §2).

Run in development:  uvicorn codeadapt.api.app:create_app --factory
"""

import hashlib
import uuid
from collections import Counter
from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from codeadapt.api import feedback, recommendation
from codeadapt.api.schemas import (
    LearnerModelView,
    LearnerNext,
    ProblemDetail,
    ProblemSummary,
    ResearchMetrics,
    ResearchSubmissionRow,
    SampleTest,
    SubmissionAccepted,
    SubmissionCreate,
    SubmissionStatus,
    SubmissionView,
    TraceView,
)
from codeadapt.config import Settings
from codeadapt.content.catalogue import Catalogue
from codeadapt.content.models import Visibility
from codeadapt.db.models import (
    DataClass,
    DiagnosisRow,
    Environment,
    ExecutionRun,
    FingerprintSetRow,
    FollowupEvaluationRow,
    Job,
    JobState,
    ProblemVersion,
    RecommendationRow,
    Role,
    Submission,
    TestObservation,
    User,
)
from codeadapt.db.session import as_utc, make_engine, make_session_factory
from codeadapt.diagnosis import Outcome
from codeadapt.learner import estimate
from codeadapt.worker.adapt import learner_attempts, skill_maps_for

ERROR_BASE = "https://codeadapt.dev/errors/"
PROBLEM_JSON = "application/problem+json"


class ApiError(Exception):
    def __init__(self, status: int, slug: str, title: str, detail: str = "") -> None:
        super().__init__(title)
        self.status, self.slug, self.title, self.detail = status, slug, title, detail


def _problem(
    request: Request, status: int, slug: str, title: str, detail: str = ""
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": ERROR_BASE + slug,
        "title": title,
        "status": status,
        "request_id": getattr(request.state, "request_id", None),
    }
    if detail:
        body["detail"] = detail
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


def create_app(
    settings: Settings | None = None,
    sessions: sessionmaker[Session] | None = None,
    catalogue: Catalogue | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    sessions = sessions or make_session_factory(make_engine(settings.database_url))
    catalogue = catalogue or Catalogue.load(settings.content_dir)
    with sessions() as s:
        catalogue.sync(s)

    app = FastAPI(
        title="CodeAdapt API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # ------------------------------------------------------------------ errors
    @app.middleware("http")
    async def request_id(request: Request, call_next: Any) -> Any:
        request.state.request_id = uuid.uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return _problem(request, exc.status, exc.slug, exc.title, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        detail = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        return _problem(request, 422, "invalid-request", "Request validation failed", detail)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(request, exc.status_code, "http-error", str(exc.detail))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        return _problem(request, 500, "internal-error", "Internal server error")

    # ------------------------------------------------------------------ dependencies
    def db() -> Iterator[Session]:
        with sessions() as session:
            yield session

    DB = Annotated[Session, Depends(db)]  # noqa: N806 - type alias

    def current_user(session: DB, x_dev_role: Annotated[str | None, Header()] = None) -> User:
        """ADR-007 stub: in dev/test the X-Dev-Role header selects a fixed dev account."""
        if not settings.dev_auth_enabled:
            raise ApiError(503, "auth-not-configured", "Authentication is not configured")
        role = Role(x_dev_role) if x_dev_role in {r.value for r in Role} else Role.STUDENT
        username = f"dev-{role.value}"
        user = session.scalar(select(User).where(User.username == username))
        if user is None:
            user = User(username=username, role=role.value, data_class=DataClass.DEV.value)
            session.add(user)
            session.commit()
        return user

    CurrentUser = Annotated[User, Depends(current_user)]  # noqa: N806 - type alias

    def researcher(user: CurrentUser) -> User:
        if user.role not in (Role.RESEARCHER.value, Role.ADMIN.value):
            raise ApiError(403, "forbidden", "Researcher role required")
        return user

    def owned_submission(session: Session, user: User, submission_id: str) -> Submission:
        sub = session.get(Submission, submission_id)
        is_staff = user.role in (Role.RESEARCHER.value, Role.ADMIN.value)
        if sub is None or (sub.user_id != user.id and not is_staff):
            raise ApiError(404, "not-found", "Submission not found")
        return sub

    # ------------------------------------------------------------------ problems
    @app.get("/api/v1/problems", response_model=list[ProblemSummary])
    def list_problems(session: DB, user: CurrentUser) -> list[ProblemSummary]:
        passed = set(
            session.scalars(
                select(ProblemVersion.slug)
                .join(Submission, Submission.problem_version == ProblemVersion.version)
                .join(DiagnosisRow, DiagnosisRow.submission_id == Submission.id)
                .where(
                    Submission.user_id == user.id,
                    DiagnosisRow.outcome == Outcome.NO_FAILURE_OBSERVED.value,
                )
            )
        )
        return [
            ProblemSummary(
                slug=p.spec.slug,
                title=p.spec.title,
                family=p.spec.family,
                no_failure_observed=p.spec.slug in passed,
            )
            for p in catalogue.problems
        ]

    @app.get("/api/v1/problems/{slug}", response_model=ProblemDetail)
    def get_problem(slug: str, _: CurrentUser) -> ProblemDetail:
        p = catalogue.by_slug.get(slug)
        if p is None:
            raise ApiError(404, "not-found", "Problem not found")
        return ProblemDetail(
            slug=p.spec.slug,
            title=p.spec.title,
            version=p.version,
            statement=p.statement,
            interface=p.spec.interface,
            starter_code=_starter(p.spec.interface),
            sample_tests=[
                SampleTest(
                    input=t.input, expected_output=t.expected, description=t.student_description
                )
                for t in p.spec.tests
                if t.visibility is Visibility.SAMPLE
            ],
        )

    # ------------------------------------------------------------------ submissions
    @app.post("/api/v1/submissions", status_code=202, response_model=SubmissionAccepted)
    def create_submission(
        body: SubmissionCreate, session: DB, user: CurrentUser
    ) -> SubmissionAccepted:
        p = catalogue.by_slug.get(body.problem_slug)
        if p is None:
            raise ApiError(404, "not-found", "Problem not found")
        sub = Submission(
            user_id=user.id,
            problem_version=p.version,
            source=body.source,
            source_sha256=hashlib.sha256(body.source.encode()).hexdigest(),
            origin="student",
            data_class=user.data_class,
        )
        session.add(sub)
        session.flush()
        session.add(Job(submission_id=sub.id))
        session.commit()
        return SubmissionAccepted(id=sub.id, status=SubmissionStatus.QUEUED)

    def submission_view(session: Session, sub: Submission) -> SubmissionView:
        problem = catalogue.by_version.get(sub.problem_version)
        slug = problem.spec.slug if problem else "unknown"
        view = SubmissionView(
            id=sub.id, problem_slug=slug, status=_status(sub.job), created_at=as_utc(sub.created_at)
        )
        diagnosis = _latest(session, sub.id)
        if diagnosis is None or problem is None or view.status is not SubmissionStatus.COMPLETED:
            return view
        run = session.get_one(ExecutionRun, diagnosis.run_id)
        observations = list(
            session.scalars(select(TestObservation).where(TestObservation.run_id == run.id))
        )
        reference = _reference(session, diagnosis)
        view.compile = feedback.compile_view(run)
        if run.compile_status == "ok":
            view.tests = feedback.test_views(problem, observations, reference)
        view.feedback = feedback.feedback_view(problem, diagnosis, view.tests)
        return view

    @app.get("/api/v1/submissions", response_model=list[SubmissionView])
    def list_submissions(
        session: DB, user: CurrentUser, problem_slug: str | None = None, limit: int = 20
    ) -> list[SubmissionView]:
        """The current user's own submissions, newest first."""
        query = select(Submission).where(Submission.user_id == user.id)
        if problem_slug is not None:
            versions = [p.version for p in catalogue.problems if p.spec.slug == problem_slug]
            query = query.where(Submission.problem_version.in_(versions))
        query = query.order_by(Submission.created_at.desc()).limit(max(1, min(limit, 50)))
        return [submission_view(session, sub) for sub in session.scalars(query)]

    @app.get("/api/v1/submissions/{submission_id}", response_model=SubmissionView)
    def get_submission(submission_id: str, session: DB, user: CurrentUser) -> SubmissionView:
        return submission_view(session, owned_submission(session, user, submission_id))

    # ------------------------------------------------------------------ adaptation
    @app.get("/api/v1/me/recommendation", response_model=LearnerNext)
    def my_recommendation(session: DB, user: CurrentUser) -> LearnerNext:
        """The current user's latest recommendation and latest follow-up verdict."""
        rec = session.scalar(
            select(RecommendationRow)
            .where(RecommendationRow.user_id == user.id)
            .order_by(RecommendationRow.id.desc())
            .limit(1)
        )
        latest = session.execute(
            select(FollowupEvaluationRow, RecommendationRow)
            .join(
                RecommendationRow, RecommendationRow.id == FollowupEvaluationRow.recommendation_id
            )
            .where(RecommendationRow.user_id == user.id)
            .order_by(FollowupEvaluationRow.id.desc())
            .limit(1)
        ).first()
        return LearnerNext(
            recommendation=recommendation.recommendation_view(catalogue, rec) if rec else None,
            last_followup=(
                recommendation.followup_view(catalogue, latest[1], latest[0]) if latest else None
            ),
        )

    # ------------------------------------------------------------------ research
    Researcher = Annotated[User, Depends(researcher)]  # noqa: N806 - type alias

    @app.get("/api/v1/research/submissions", response_model=list[ResearchSubmissionRow])
    def research_submissions(
        session: DB,
        _: Researcher,
        problem_slug: str | None = None,
        outcome: str | None = None,
        data_class: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ResearchSubmissionRow]:
        """Every user's submissions, newest first, with optional filters."""
        query = (
            select(Submission, User, ProblemVersion.slug)
            .join(User, User.id == Submission.user_id)
            .join(ProblemVersion, ProblemVersion.version == Submission.problem_version)
        )
        if problem_slug:
            query = query.where(ProblemVersion.slug == problem_slug)
        if data_class:
            query = query.where(Submission.data_class == data_class)
        if outcome:
            latest = (
                select(DiagnosisRow.submission_id)
                .where(DiagnosisRow.outcome == outcome)
                .scalar_subquery()
            )
            query = query.where(Submission.id.in_(latest))
        query = (
            query.order_by(Submission.created_at.desc(), Submission.id)
            .limit(max(1, min(limit, 200)))
            .offset(max(0, offset))
        )
        rows = []
        for sub, user, slug in session.execute(query):
            diagnosis = _latest(session, sub.id)
            rec = _by_submission(session, RecommendationRow, sub.id)
            ev = _by_submission(session, FollowupEvaluationRow, sub.id)
            rows.append(
                ResearchSubmissionRow(
                    id=sub.id,
                    created_at=as_utc(sub.created_at),
                    username=user.username,
                    data_class=sub.data_class,
                    origin=sub.origin,
                    problem_slug=slug,
                    status=_status(sub.job),
                    outcome=diagnosis.outcome if diagnosis else None,
                    selected_model=diagnosis.selected_model if diagnosis else None,
                    support=diagnosis.support if diagnosis else None,
                    recommendation_rule=rec.rule if rec else None,
                    recommended_problem=rec.problem_slug if rec else None,
                    review_flag=bool(rec and rec.review_flag),
                    followup_verdict=ev.verdict if ev else None,
                )
            )
        return rows

    @app.get("/api/v1/research/metrics", response_model=ResearchMetrics)
    def research_metrics(
        session: DB, _: Researcher, data_class: str | None = None
    ) -> ResearchMetrics:
        """Counts over stored evidence; latest diagnosis per submission."""
        subs = select(Submission.id, ProblemVersion.slug).join(
            ProblemVersion, ProblemVersion.version == Submission.problem_version
        )
        if data_class:
            subs = subs.where(Submission.data_class == data_class)
        slugs: dict[str, str] = {row[0]: row[1] for row in session.execute(subs)}
        outcomes: Counter[str] = Counter()
        by_problem: dict[str, Counter[str]] = {}
        latest: dict[str, str] = {}
        for sid, value in session.execute(
            select(DiagnosisRow.submission_id, DiagnosisRow.outcome)
            .where(DiagnosisRow.submission_id.in_(list(slugs)))
            .order_by(DiagnosisRow.id)
        ):
            latest[sid] = value
        for sid, value in latest.items():
            outcomes[value] += 1
            by_problem.setdefault(slugs[sid], Counter())[value] += 1
        recs = list(
            session.scalars(
                select(RecommendationRow).where(RecommendationRow.submission_id.in_(list(slugs)))
            )
        )
        verdicts = Counter(
            session.scalars(
                select(FollowupEvaluationRow.verdict).where(
                    FollowupEvaluationRow.submission_id.in_(list(slugs))
                )
            )
        )
        return ResearchMetrics(
            data_class=data_class,
            submissions=len(slugs),
            outcomes=dict(sorted(outcomes.items())),
            outcomes_by_problem={k: dict(sorted(v.items())) for k, v in sorted(by_problem.items())},
            recommendations_by_rule=dict(sorted(Counter(r.rule for r in recs).items())),
            flagged_for_review=sum(r.review_flag for r in recs),
            followup_verdicts=dict(sorted(verdicts.items())),
        )

    @app.get("/api/v1/research/submissions/{submission_id}/trace", response_model=TraceView)
    def trace(submission_id: str, session: DB, _: Researcher) -> TraceView:
        sub = session.get(Submission, submission_id)
        if sub is None:
            raise ApiError(404, "not-found", "Submission not found")
        diagnosis = _latest(session, sub.id)
        run = session.get(ExecutionRun, diagnosis.run_id) if diagnosis else None
        env = session.get(Environment, run.environment_id) if run else None
        fps = (
            session.get(FingerprintSetRow, diagnosis.fingerprint_set_id)
            if diagnosis and diagnosis.fingerprint_set_id
            else None
        )
        runs = list(
            session.scalars(
                select(ExecutionRun)
                .where(ExecutionRun.submission_id == sub.id)
                .order_by(ExecutionRun.id)
            )
        )
        observations = list(
            session.scalars(
                select(TestObservation)
                .where(TestObservation.run_id.in_([r.id for r in runs]))
                .order_by(TestObservation.run_id, TestObservation.id)
            )
        )
        return TraceView(
            submission=_row(sub),
            job=_row(sub.job),
            environment=env.info if env else None,
            execution_runs=[_row(r) for r in runs],
            observations=[_row(o) for o in observations],
            diagnosis=_row(diagnosis) if diagnosis else None,
            content_validation=fps.report if fps else None,
            recommendation=_row(rec)
            if (rec := _by_submission(session, RecommendationRow, sub.id))
            else None,
            followup_evaluation=(
                _row(ev) if (ev := _by_submission(session, FollowupEvaluationRow, sub.id)) else None
            ),
        )

    @app.get("/api/v1/research/learner-model", response_model=LearnerModelView)
    def learner_model(username: str, session: DB, _: Researcher) -> LearnerModelView:
        """LM1 estimates for one learner, over the submissions of the learner's data class."""
        learner = session.scalar(select(User).where(User.username == username))
        if learner is None:
            raise ApiError(404, "not-found", "User not found")
        attempts = list(learner_attempts(session, learner.id, learner.data_class).values())
        problems = {p.spec.slug: p.spec for p in catalogue.problems}
        return LearnerModelView(
            username=learner.username,
            data_class=learner.data_class,
            attempts=len(attempts),
            estimate=estimate(attempts, problems, skill_maps_for(session, attempts)),
        )

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def _status(job: Job) -> SubmissionStatus:
    return {
        JobState.QUEUED.value: SubmissionStatus.QUEUED,
        JobState.RUNNING.value: SubmissionStatus.RUNNING,
        JobState.DONE.value: SubmissionStatus.COMPLETED,
        JobState.FAILED.value: SubmissionStatus.FAILED,
    }[job.state]


def _latest(session: Session, submission_id: str) -> DiagnosisRow | None:
    return session.scalar(
        select(DiagnosisRow)
        .where(DiagnosisRow.submission_id == submission_id)
        .order_by(DiagnosisRow.id.desc())
        .limit(1)
    )


def _by_submission(
    session: Session, table: type[RecommendationRow] | type[FollowupEvaluationRow], sid: str
) -> Any:
    return session.scalar(
        select(table).where(table.submission_id == sid).order_by(table.id.desc()).limit(1)
    )


def _reference(session: Session, diagnosis: DiagnosisRow) -> dict[str, tuple[str, str]]:
    if diagnosis.fingerprint_set_id is None:
        return {}
    fps = session.get_one(FingerprintSetRow, diagnosis.fingerprint_set_id)
    tests = fps.data["reference"]["tests"]
    return {k: (t["runs"][0]["kind"], t["runs"][0]["detail"]) for k, t in tests.items()}


def _row(obj: Any) -> dict[str, Any]:
    return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}


def _starter(interface: str) -> str:
    """Editor starting point derived from the interface declaration."""
    signature = interface.strip().removesuffix(";")
    return f"#include <vector>\n\n{signature} {{\n    // Your code here.\n}}\n"
