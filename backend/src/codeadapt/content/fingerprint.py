"""Execute the reference and every error model on every test: measured predictions.

Fingerprints are never hand-written. They are tied to the environment they were measured
in, and each test is run `repeats` times so non-determinism is detected, not assumed away.
"""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, ConfigDict

from codeadapt.content.loader import LoadedProblem
from codeadapt.evidence.signature import Signature, signature_of
from codeadapt.execution.backend import SandboxBackend
from codeadapt.execution.models import BuildProfile, CompileResult, CompileStatus, EnvironmentInfo

REFERENCE = "__reference__"


class TestFingerprint(BaseModel):
    __test__ = False
    model_config = ConfigDict(frozen=True)

    runs: tuple[Signature, ...]

    @property
    def deterministic(self) -> bool:
        return len(set(self.runs)) == 1

    @property
    def signature(self) -> Signature | None:
        """The program's behaviour on this test, or None if it was not reproducible."""
        return self.runs[0] if self.deterministic else None


class ProgramFingerprint(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    compile: CompileResult
    tests: dict[str, TestFingerprint]  # empty when compilation failed

    @property
    def compiled(self) -> bool:
        return self.compile.status is CompileStatus.OK


class FingerprintSet(BaseModel):
    model_config = ConfigDict(frozen=True)

    problem_slug: str
    problem_version: str
    environment: EnvironmentInfo
    repeats: int
    reference: ProgramFingerprint
    models: dict[str, ProgramFingerprint]


async def fingerprint_program(
    sandbox: SandboxBackend,
    problem: LoadedProblem,
    label: str,
    source: str,
    repeats: int = 2,
) -> ProgramFingerprint:
    async with sandbox.job() as job:
        compiled = await job.compile(problem.program(source), BuildProfile.STANDARD)
        if compiled.status is not CompileStatus.OK:
            return ProgramFingerprint(label=label, compile=compiled, tests={})

        async def one(stdin: bytes) -> Signature:
            return signature_of(await job.run(stdin, BuildProfile.STANDARD))

        tests = problem.spec.tests
        signatures = await asyncio.gather(
            *(one(t.input.encode()) for t in tests for _ in range(repeats))
        )
    return ProgramFingerprint(
        label=label,
        compile=compiled,
        tests={
            t.key: TestFingerprint(runs=tuple(signatures[i * repeats : (i + 1) * repeats]))
            for i, t in enumerate(tests)
        },
    )


async def fingerprint_problem(
    sandbox: SandboxBackend, problem: LoadedProblem, repeats: int = 2
) -> FingerprintSet:
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    environment = await sandbox.environment()
    reference = await fingerprint_program(sandbox, problem, REFERENCE, problem.reference, repeats)
    models = await asyncio.gather(
        *(
            fingerprint_program(sandbox, problem, key, source, repeats)
            for key, source in problem.error_model_sources.items()
        )
    )
    return FingerprintSet(
        problem_slug=problem.spec.slug,
        problem_version=problem.version,
        environment=environment,
        repeats=repeats,
        reference=reference,
        models={m.label: m for m in models},
    )
