"""One submission through execution, evidence recording and diagnosis."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
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
from codeadapt.diagnosis import DiagnosticInput, DiagnosticMethod, Observation
from codeadapt.evidence import Signature, signature_of
from codeadapt.evidence.reliability import assess
from codeadapt.execution.backend import SandboxBackend, SandboxUnavailableError
from codeadapt.execution.models import (
    BuildProfile,
    CompileResult,
    CompileStatus,
    EnvironmentInfo,
    RunResult,
)
from codeadapt.worker.adapt import adapt

log = logging.getLogger(__name__)


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

    # ------------------------------------------------------------------ job handling
    async def handle(self, job: Job) -> None:
        """Process one claimed job and record its final state. Never raises for job errors."""
        with self.sessions() as session:
            try:
                await self.process(session, job.submission_id)
            except SandboxUnavailableError as exc:
                log.warning("sandbox unavailable; requeueing job %s: %s", job.id, exc)
                session.rollback()
                queue.requeue(session, job, f"sandbox unavailable: {exc}")
                return
            except Exception as exc:
                log.exception("job %s failed", job.id)
                session.rollback()
                queue.finish(
                    session, job, state=JobState.FAILED, error=f"{type(exc).__name__}: {exc}"
                )
                return
            queue.finish(session, job, state=JobState.DONE)

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
        tests = problem.spec.tests
        program = problem.program(submission.source)
        started = utcnow()
        standard: dict[str, RunResult] = {}
        repeats: dict[str, list[RunResult]] = {}
        sanitized: dict[str, RunResult] | None = None
        async with self.sandbox.job() as job:
            compiled = await job.compile(program, BuildProfile.STANDARD)
            if compiled.status is CompileStatus.INFRASTRUCTURE_ERROR:
                raise SandboxUnavailableError(compiled.detail or "compile container did not start")
            sanitize_compile = None
            if compiled.status is CompileStatus.OK:
                standard = dict(
                    zip(
                        (t.key for t in tests),
                        await asyncio.gather(
                            *(job.run(t.input.encode(), BuildProfile.STANDARD) for t in tests)
                        ),
                        strict=True,
                    )
                )
                # Reliability channel 1: rerun every failing test once (methodology §3).
                failing = [t for t in tests if signature_of(standard[t.key]) != reference[t.key]]
                again = await asyncio.gather(
                    *(job.run(t.input.encode(), BuildProfile.STANDARD) for t in failing)
                )
                repeats = {t.key: [r] for t, r in zip(failing, again, strict=True)}
                # Reliability channel 2: ASan + UBSan build over every test.
                sanitize_compile = await job.compile(program, BuildProfile.SANITIZE)
                if sanitize_compile.status is CompileStatus.OK:
                    sanitized = dict(
                        zip(
                            (t.key for t in tests),
                            await asyncio.gather(
                                *(job.run(t.input.encode(), BuildProfile.SANITIZE) for t in tests)
                            ),
                            strict=True,
                        )
                    )
        finished = utcnow()
        run = _run_row(submission.id, environment.id, compiled, started, finished)
        session.add(run)
        session.flush()
        assessment = assess(standard, repeats, sanitized)
        observations: list[Observation] = []
        for key, result in standard.items():
            sig = signature_of(result)
            reason = assessment[key].excluded_reason
            observations.append(Observation(test_key=key, signature=sig, excluded_reason=reason))
            session.add(_observation_row(run.id, key, 0, result, sig, reason))
            for i, rerun in enumerate(repeats.get(key, ()), start=1):
                session.add(_observation_row(run.id, key, i, rerun, signature_of(rerun), None))
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
        # Adaptation runs on committed evidence; a failure here must not lose the diagnosis.
        try:
            adapt(session, submission, row, self.catalogue, self.policy)
            session.commit()
        except Exception:
            log.exception("adaptation failed for submission %s", submission.id)
            session.rollback()
        return row

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
                fps = await fingerprint_problem(self.sandbox, problem)
                report = validate_fingerprints(problem.spec, fps)
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
