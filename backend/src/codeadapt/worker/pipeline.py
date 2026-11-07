"""One submission through execution, evidence recording and diagnosis."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from codeadapt.adaptation import PolicyV1
from codeadapt.content.catalogue import Catalogue
from codeadapt.content.fingerprint import FingerprintSet, fingerprint_problem
from codeadapt.content.loader import LoadedProblem
from codeadapt.content.validate import validate_fingerprints
from codeadapt.db import queue
from codeadapt.db.models import (
    DiagnosisRow,
    Environment,
    ExecutionRun,
    FingerprintSetRow,
    Job,
    JobState,
    Submission,
    TestObservation,
    utcnow,
)
from codeadapt.diagnosis import DiagnosticInput, DiagnosticMethod
from codeadapt.evidence import Signature, signature_of
from codeadapt.evidence.collect import collect_evidence
from codeadapt.evidence.reliability import EVIDENCE_RULES_VERSION
from codeadapt.execution.backend import SandboxBackend, SandboxUnavailableError
from codeadapt.execution.models import (
    CompileResult,
    CompileStatus,
    EnvironmentInfo,
    RunResult,
)
from codeadapt.logs import redact
from codeadapt.worker.adapt import adapt
from codeadapt.worker.recovery import ADAPTATION_FAILED

log = logging.getLogger(__name__)

__all__ = ["ADAPTATION_FAILED", "ContentUnavailableError", "Pipeline"]


class ContentUnavailableError(RuntimeError):
    """The problem version is unknown to this worker or its content failed validation."""


class Pipeline:
    def __init__(
        self,
        sandbox: SandboxBackend,
        sessions: sessionmaker[Session],
        catalogue: Catalogue,
        method: DiagnosticMethod,
        policy: PolicyV1 | None = None,
    ) -> None:
        self.sandbox = sandbox
        self.sessions = sessions
        self.catalogue = catalogue
        self.method = method
        self.policy = policy or PolicyV1()
        self._fingerprint_lock = asyncio.Lock()
        # submission id -> why adaptation failed after its diagnosis was committed
        self.adaptation_errors: dict[str, str] = {}

    # ------------------------------------------------------------------ job handling
    async def handle(self, job: Job) -> None:
        """Process one claimed job and record its final state. Never raises for job errors."""
        with self.sessions() as session:
            try:
                existing = self._existing_diagnosis(session, job.submission_id)
                if existing is not None:
                    # A redelivered job (a worker died after committing): do not run the
                    # submission again, which would add a second, possibly different diagnosis
                    # and a second recommendation.
                    log.info("job %s already has diagnosis %s", job.id, existing.id)
                else:
                    await self.process(session, job.submission_id)
            except SandboxUnavailableError as exc:
                self.adaptation_errors.pop(job.submission_id, None)
                log.warning("sandbox unavailable; requeueing job %s: %s", job.id, exc)
                session.rollback()
                if not queue.requeue(session, job, f"sandbox unavailable: {_error_text(exc)}"):
                    log.warning("job %s was reclaimed by another worker", job.id)
                return
            except Exception as exc:
                self.adaptation_errors.pop(job.submission_id, None)
                log.exception("job %s failed", job.id)
                session.rollback()
                if not queue.finish(
                    session, job, state=JobState.FAILED, error=_error_text(exc, with_type=True)
                ):
                    log.warning("job %s was reclaimed by another worker", job.id)
                return
            adaptation_error = self.adaptation_errors.pop(job.submission_id, None)
            marker = (
                f"{ADAPTATION_FAILED}{adaptation_error}" if adaptation_error is not None else None
            )
            # DONE: the diagnosis is recorded; the marker says no recommendation was made.
            if not queue.finish(session, job, state=JobState.DONE, error=marker):
                log.warning("job %s was reclaimed by another worker", job.id)

    async def warm_up(self) -> dict[str, bool]:
        """Measure and store the fingerprints of every catalogue version in this environment.

        Uses the same cached path as the first submission to a problem, so a class session
        does not wait 1-2 minutes per problem (audit D7). Returns slug@version -> valid.
        """
        results: dict[str, bool] = {}
        with self.sessions() as session:
            environment = self._environment(session, await self.sandbox.environment())
            for problem in self.catalogue.problems:
                key = f"{problem.spec.slug}@{problem.version[:12]}"
                try:
                    await self._fingerprints(session, problem, environment)
                    results[key] = True
                except ContentUnavailableError:
                    results[key] = False
        return results

    def _existing_diagnosis(self, session: Session, submission_id: str) -> DiagnosisRow | None:
        """A diagnosis this worker's method version already recorded for the submission."""
        return session.scalars(
            select(DiagnosisRow)
            .where(
                DiagnosisRow.submission_id == submission_id,
                DiagnosisRow.method == self.method.name,
                DiagnosisRow.method_version == self.method.version,
            )
            .limit(1)
        ).first()

    async def process(self, session: Session, submission_id: str) -> DiagnosisRow:
        submission = session.get_one(Submission, submission_id)
        problem = self.catalogue.by_version.get(submission.problem_version)
        if problem is None:
            raise ContentUnavailableError(
                f"problem version {submission.problem_version} is not in this worker's catalogue"
            )
        env_info = await self.sandbox.environment()
        environment = self._environment(session, env_info)
        fingerprints, fps_row = await self._fingerprints(session, problem, environment)

        reference = _predictions(fingerprints, None)
        started = utcnow()
        evidence = await collect_evidence(self.sandbox, problem, submission.source, reference)
        finished = utcnow()
        compiled, sanitize_compile = evidence.compiled, evidence.sanitize_compile
        standard, repeats, sanitized = evidence.standard, evidence.repeats, evidence.sanitized
        run = _run_row(submission.id, environment.id, compiled, started, finished)
        session.add(run)
        session.flush()
        assessment = evidence.assessment()
        observations = evidence.observations()
        for obs in observations:
            result = standard[obs.test_key]
            session.add(
                _observation_row(
                    run.id, obs.test_key, 0, result, obs.signature, obs.excluded_reason
                )
            )
            for i, rerun in enumerate(repeats.get(obs.test_key, ()), start=1):
                session.add(
                    _observation_row(run.id, obs.test_key, i, rerun, signature_of(rerun), None)
                )
        if sanitize_compile is not None:
            sanitize_run = _run_row(
                submission.id, environment.id, sanitize_compile, started, finished
            )
            session.add(sanitize_run)
            session.flush()
            for key, result in (sanitized or {}).items():
                session.add(
                    _observation_row(sanitize_run.id, key, 0, result, signature_of(result), None)
                )

        diagnosis = self.method.diagnose(
            DiagnosticInput(
                problem_version=problem.version,
                compiled=compiled.status is CompileStatus.OK,
                observations=tuple(observations),
                reference=reference,
                models={k: _predictions(fingerprints, k) for k in fingerprints.models},
            )
        )
        rationale = {
            **diagnosis.rationale,
            "reliability": {
                "evidence_rules_version": EVIDENCE_RULES_VERSION,
                "sanitizer_available": sanitized is not None,
                "sanitizer_compile_status": (
                    sanitize_compile.status.value if sanitize_compile is not None else None
                ),
                "repeated_tests": sorted(repeats),
                "findings": {k: a.finding.model_dump() for k, a in assessment.items() if a.finding},
            },
        }
        row = DiagnosisRow(
            submission_id=submission.id,
            run_id=run.id,
            fingerprint_set_id=fps_row.id,
            method=diagnosis.method,
            method_version=diagnosis.method_version,
            outcome=diagnosis.outcome.value,
            selected_model=diagnosis.selected_model,
            candidates=list(diagnosis.candidates),
            support=diagnosis.support,
            rationale=rationale,
        )
        session.add(row)
        session.commit()
        error = self.adapt_after_diagnosis(session, submission, row)
        if error is not None:
            self.adaptation_errors[submission.id] = error
        return row

    def adapt_after_diagnosis(
        self, session: Session, submission: Submission, row: DiagnosisRow
    ) -> str | None:
        """Run the adaptive policy on the committed diagnosis.

        A failure here must not lose the diagnosis: it is rolled back alone and returned as
        text, which `handle` records on the job (ADR-042, audit D6). Nothing about what is
        diagnosed or recommended changes; the failure only stops being silent.
        """
        try:
            adapt(session, submission, row, self.catalogue, self.policy)
            session.commit()
        except Exception as exc:
            log.exception(
                "adaptation failed for submission %s",
                submission.id,
                extra={"event": "adaptation_failed", "submission_id": submission.id},
            )
            session.rollback()
            return _error_text(exc, with_type=True)
        return None

    # ------------------------------------------------------------------ provenance
    @staticmethod
    def _environment(session: Session, info: EnvironmentInfo) -> Environment:
        payload = info.model_dump(mode="json")
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        existing = session.scalar(select(Environment).where(Environment.digest == digest))
        if existing is not None:
            return existing
        row = Environment(digest=digest, info=payload)
        session.add(row)
        try:
            session.commit()
        except IntegrityError:  # another worker registered it first
            session.rollback()
            return session.scalars(select(Environment).where(Environment.digest == digest)).one()
        return row

    async def _fingerprints(
        self, session: Session, problem: LoadedProblem, environment: Environment
    ) -> tuple[FingerprintSet, FingerprintSetRow]:
        """Measured predictions for this content version in this environment (cached)."""

        def lookup() -> FingerprintSetRow | None:
            return session.scalar(
                select(FingerprintSetRow).where(
                    FingerprintSetRow.problem_version == problem.version,
                    FingerprintSetRow.environment_id == environment.id,
                )
            )

        async with self._fingerprint_lock:
            row = lookup()
            if row is None:
                log.info(
                    "measuring fingerprints for %s in environment %s",
                    problem.spec.slug,
                    environment.id,
                )
                started = time.monotonic()
                fps = await fingerprint_problem(self.sandbox, problem)
                report = validate_fingerprints(problem.spec, fps)
                log.info(
                    "measured fingerprints for %s in %.0f s (valid: %s)",
                    problem.spec.slug,
                    time.monotonic() - started,
                    report.ok,
                )
                row = FingerprintSetRow(
                    problem_version=problem.version,
                    environment_id=environment.id,
                    valid=report.ok,
                    data=fps.model_dump(mode="json"),
                    report=report.model_dump(mode="json"),
                )
                session.add(row)
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    row = lookup()
                    if row is None:  # pragma: no cover - constraint implies a row exists
                        raise
        if not row.valid:
            raise ContentUnavailableError(
                f"content {problem.spec.slug}@{problem.version[:12]} failed validation: "
                f"{row.report.get('errors')}"
            )
        return FingerprintSet.model_validate(row.data), row


MAX_ERROR_CHARS = 2000


def _error_text(exc: BaseException, *, with_type: bool = False) -> str:
    """An exception as stored in `jobs.last_error`: redacted and bounded (ADR-042)."""
    text = f"{type(exc).__name__}: {exc}" if with_type else str(exc)
    return redact(text)[:MAX_ERROR_CHARS]


def _predictions(fps: FingerprintSet, model: str | None) -> dict[str, Signature]:
    program = fps.reference if model is None else fps.models[model]
    out: dict[str, Signature] = {}
    for key, test in program.tests.items():
        sig = test.signature
        if sig is None:  # validation rejects non-determinism, so this cannot be reached
            raise ContentUnavailableError(
                f"non-deterministic fingerprint for {program.label}/{key}"
            )
        out[key] = sig
    return out


def _run_row(
    submission_id: str,
    environment_id: int,
    compiled: CompileResult,
    started: datetime,
    finished: datetime,
) -> ExecutionRun:
    return ExecutionRun(
        submission_id=submission_id,
        environment_id=environment_id,
        profile=compiled.profile.value,
        compile_status=compiled.status.value,
        compile_flags=list(compiled.flags),
        compile_exit_code=compiled.exit_code,
        compile_diagnostics=compiled.diagnostics,
        compile_diagnostics_truncated=compiled.diagnostics_truncated,
        compile_wall_ms=compiled.wall_ms,
        started_at=started,
        finished_at=finished,
    )


def _observation_row(
    run_id: int,
    test_key: str,
    repeat_index: int,
    result: RunResult,
    sig: Signature,
    excluded_reason: str | None,
) -> TestObservation:
    return TestObservation(
        run_id=run_id,
        test_key=test_key,
        repeat_index=repeat_index,
        status=result.status.value,
        signature_kind=sig.kind.value,
        signature_detail=sig.detail,
        exit_code=result.exit_code,
        signal=result.signal,
        stdout=result.stdout,
        stdout_sha256=hashlib.sha256(result.stdout.encode()).hexdigest(),
        stdout_truncated=result.stdout_truncated,
        stderr=result.stderr,
        stderr_truncated=result.stderr_truncated,
        wall_ms=result.wall_ms,
        oom_killed=result.oom_killed,
        timed_out=result.timed_out,
        excluded_reason=excluded_reason,
    )
