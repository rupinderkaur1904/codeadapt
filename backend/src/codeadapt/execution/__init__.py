"""Sandboxed compilation and execution of untrusted C++ (no domain knowledge here)."""

from codeadapt.execution.backend import SandboxBackend, SandboxJob, SandboxUnavailableError
from codeadapt.execution.docker import DockerSandbox, DockerSandboxConfig
from codeadapt.execution.models import (
    BuildProfile,
    CompileLimits,
    CompileResult,
    CompileStatus,
    EnvironmentInfo,
    RunLimits,
    RunResult,
    RunStatus,
    SourceFile,
)

__all__ = [
    "BuildProfile",
    "CompileLimits",
    "CompileResult",
    "CompileStatus",
    "DockerSandbox",
    "DockerSandboxConfig",
    "EnvironmentInfo",
    "RunLimits",
    "RunResult",
    "RunStatus",
    "SandboxBackend",
    "SandboxJob",
    "SandboxUnavailableError",
    "SourceFile",
]
