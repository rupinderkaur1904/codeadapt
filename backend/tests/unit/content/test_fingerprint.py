"""Fingerprint measurement re-measures infrastructure errors, never program behaviour."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from codeadapt.content import load_problem
from codeadapt.content.fingerprint import INFRA_RETRIES, fingerprint_program
from codeadapt.evidence import OutcomeKind
from codeadapt.execution.models import (
    BuildProfile,
    CompileResult,
    CompileStatus,
    RunResult,
    RunStatus,
    SourceFile,
)
from tests.paths import DEMO_CONTENT

PROBLEM = load_problem(DEMO_CONTENT / "lower-bound")


def result(status: RunStatus, stdout: str = "") -> RunResult:
    return RunResult(
        status=status,
        exit_code=0,
        signal=None,
        stdout=stdout,
        stdout_truncated=False,
        stderr="",
        stderr_truncated=False,
        wall_ms=1,
        oom_killed=False,
        timed_out=False,
    )


class ScriptedJob:
    """Answers runs from a per-input script; unscripted inputs print "1"."""

    def __init__(self, script: dict[str, list[RunResult]]) -> None:
        self.script = script
        self.runs = 0

    async def compile(self, sources: list[SourceFile], profile: BuildProfile) -> CompileResult:
        ok = profile is BuildProfile.STANDARD
        return CompileResult(
            status=CompileStatus.OK if ok else CompileStatus.INFRASTRUCTURE_ERROR,
            profile=profile,
            flags=(),
            exit_code=0,
            diagnostics="",
            diagnostics_truncated=False,
            wall_ms=1,
        )

    async def run(self, stdin: bytes, profile: BuildProfile, limits: object = None) -> RunResult:
        self.runs += 1
        queue = self.script.get(stdin.decode())
        return queue.pop(0) if queue else result(RunStatus.OK, "1")


class ScriptedSandbox:
    def __init__(self, job: ScriptedJob) -> None:
        self._job = job

    @asynccontextmanager
    async def job(self) -> AsyncIterator[ScriptedJob]:
        yield self._job


INFRA = result(RunStatus.INFRASTRUCTURE_ERROR)


async def test_infrastructure_errors_are_measured_again() -> None:
    first = PROBLEM.spec.tests[0]
    job = ScriptedJob({first.input: [INFRA, result(RunStatus.OK, "7")]})
    fp = await fingerprint_program(ScriptedSandbox(job), PROBLEM, "x", "", repeats=1)  # type: ignore[arg-type]
    sig = fp.tests[first.key].signature
    assert sig is not None
    assert (sig.kind, sig.detail) == (OutcomeKind.OUTPUT, "7")


async def test_persistent_infrastructure_errors_are_kept_after_the_limit() -> None:
    first = PROBLEM.spec.tests[0]
    job = ScriptedJob({first.input: [INFRA] * INFRA_RETRIES})
    fp = await fingerprint_program(ScriptedSandbox(job), PROBLEM, "x", "", repeats=1)  # type: ignore[arg-type]
    sig = fp.tests[first.key].signature
    assert sig is not None
    assert sig.kind is OutcomeKind.INFRASTRUCTURE_ERROR


async def test_differing_program_outputs_are_not_retried() -> None:
    first = PROBLEM.spec.tests[0]
    job = ScriptedJob({first.input: [result(RunStatus.OK, "1"), result(RunStatus.OK, "2")]})
    fp = await fingerprint_program(ScriptedSandbox(job), PROBLEM, "x", "", repeats=2)  # type: ignore[arg-type]
    assert not fp.tests[first.key].deterministic
