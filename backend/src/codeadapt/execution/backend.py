"""Backend-neutral sandbox interface.

Higher layers depend only on these protocols so that the isolation mechanism (Docker with
runc, Docker with gVisor, a future microVM backend) can change without touching them.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from codeadapt.execution.models import (
    BuildProfile,
    CompileResult,
    EnvironmentInfo,
    RunLimits,
    RunResult,
    SourceFile,
)


class SandboxUnavailableError(RuntimeError):
    """The isolation backend itself is not usable (daemon down, image missing, …).

    This is an infrastructure condition, never evidence about a submission.
    """


class SandboxJob(Protocol):
    """One isolated workspace: compile once, then run the produced binary many times."""

    async def compile(self, sources: list[SourceFile], profile: BuildProfile) -> CompileResult: ...

    async def run(
        self, stdin: bytes, profile: BuildProfile, limits: RunLimits | None = None
    ) -> RunResult: ...


class SandboxBackend(Protocol):
    async def environment(self) -> EnvironmentInfo: ...

    def job(self) -> AbstractAsyncContextManager[SandboxJob]: ...

    async def reap(self) -> int: ...
