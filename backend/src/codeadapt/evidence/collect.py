"""Execute one submission and collect every evidence channel (methodology §3).

Shared by the worker pipeline and the evaluation harness so both see exactly the same
evidence for the same source.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field

from codeadapt.content.loader import LoadedProblem
from codeadapt.diagnosis import Observation
from codeadapt.evidence.reliability import TestReliability, assess
from codeadapt.evidence.signature import Signature, signature_of
from codeadapt.execution.backend import SandboxBackend, SandboxUnavailableError
from codeadapt.execution.models import (
    BuildProfile,
    CompileResult,
    CompileStatus,
    RunResult,
    RunStatus,
)

# A run-level infrastructure error says nothing about the submission, so it is measured
# again, at most this many times in total (the same bound as fingerprinting). A persistent
# one still makes the whole attempt an execution error (methodology §4, rule 2).
INFRA_ATTEMPTS = 3


@dataclass
class SubmissionEvidence:
    compiled: CompileResult
    sanitize_compile: CompileResult | None = None
    standard: dict[str, RunResult] = field(default_factory=dict)
    # Extra standard-build runs of tests whose first signature differed from the reference.
    repeats: dict[str, list[RunResult]] = field(default_factory=dict)
    # None when the sanitizer build did not compile or was not attempted.
    sanitized: dict[str, RunResult] | None = None

    @property
    def ok(self) -> bool:
        return self.compiled.status is CompileStatus.OK

    def assessment(self) -> dict[str, TestReliability]:
        return assess(self.standard, self.repeats, self.sanitized)

    def observations(self) -> list[Observation]:
        assessment = self.assessment()
        return [
            Observation(
                test_key=key,
                signature=signature_of(result),
                excluded_reason=assessment[key].excluded_reason,
            )
            for key, result in self.standard.items()
        ]


async def collect_evidence(
    sandbox: SandboxBackend,
    problem: LoadedProblem,
    source: str,
    reference: Mapping[str, Signature],
) -> SubmissionEvidence:
    """Compile, run every test, repeat failing tests once, run the sanitizer build.

    Raises SandboxUnavailableError when the compile container could not start, since
    that says nothing about the submission.
    """
    tests = problem.spec.tests
    program = problem.program(source)
    async with sandbox.job() as job:
        compiled = await job.compile(program, BuildProfile.STANDARD)
        if compiled.status is CompileStatus.INFRASTRUCTURE_ERROR:
            raise SandboxUnavailableError(compiled.detail or "compile container did not start")
        evidence = SubmissionEvidence(compiled=compiled)
        if compiled.status is not CompileStatus.OK:
            return evidence

        async def run(stdin: bytes, profile: BuildProfile) -> RunResult:
            for _ in range(INFRA_ATTEMPTS):
                result = await job.run(stdin, profile)
                if result.status is not RunStatus.INFRASTRUCTURE_ERROR:
                    break
            return result

        async def run_all(profile: BuildProfile) -> dict[str, RunResult]:
            results = await asyncio.gather(*(run(t.input.encode(), profile) for t in tests))
            return dict(zip((t.key for t in tests), results, strict=True))

        evidence.standard = await run_all(BuildProfile.STANDARD)
        # Reliability channel 1: rerun every failing test once.
        failing = [
            t for t in tests if signature_of(evidence.standard[t.key]) != reference.get(t.key)
        ]
        again = await asyncio.gather(
            *(run(t.input.encode(), BuildProfile.STANDARD) for t in failing)
        )
        evidence.repeats = {t.key: [r] for t, r in zip(failing, again, strict=True)}
        # Reliability channel 2: ASan + UBSan build over every test.
        evidence.sanitize_compile = await job.compile(program, BuildProfile.SANITIZE)
        if evidence.sanitize_compile.status is CompileStatus.OK:
            evidence.sanitized = await run_all(BuildProfile.SANITIZE)
    return evidence
