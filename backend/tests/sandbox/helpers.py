from __future__ import annotations

from codeadapt.execution import (
    BuildProfile,
    CompileStatus,
    DockerSandbox,
    RunLimits,
    RunResult,
    SourceFile,
)


async def compile_and_run(
    sandbox: DockerSandbox,
    source: str,
    stdin: bytes = b"",
    *,
    profile: BuildProfile = BuildProfile.STANDARD,
    limits: RunLimits | None = None,
) -> RunResult:
    async with sandbox.job() as job:
        compiled = await job.compile([SourceFile(name="main.cpp", content=source)], profile)
        assert compiled.status is CompileStatus.OK, compiled.diagnostics
        return await job.run(stdin, profile, limits)
