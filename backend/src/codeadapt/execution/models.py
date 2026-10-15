"""Typed inputs and results of sandboxed compilation and execution.

These models are the contract between the execution layer and everything above it. They
describe *what happened*, never what it means for a student: interpretation belongs to
the evidence and diagnosis layers.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Conservative file-name rule: no paths, no shell metacharacters, C++ source/header only.
_SOURCE_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}\.(cpp|cc|h|hpp)$")


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SourceFile(_Frozen):
    """One file placed in the compile directory. Names are validated host-side."""

    name: str
    content: str

    @field_validator("name")
    @classmethod
    def _valid_name(cls, value: str) -> str:
        if not _SOURCE_NAME.fullmatch(value):
            raise ValueError(f"invalid source file name: {value!r}")
        return value


class BuildProfile(StrEnum):
    """Named compiler configurations. Flags are fixed per profile for reproducibility."""

    STANDARD = "standard"
    SANITIZE = "sanitize"


class CompileStatus(StrEnum):
    OK = "ok"
    ERROR = "error"  # the compiler rejected the program
    TIME_LIMIT = "time_limit"
    MEMORY_LIMIT = "memory_limit"
    OUTPUT_LIMIT = "output_limit"
    INFRASTRUCTURE_ERROR = "infrastructure_error"


class RunStatus(StrEnum):
    OK = "ok"  # exited with status 0; says nothing about whether the output is right
    RUNTIME_ERROR = "runtime_error"
    TIME_LIMIT = "time_limit"
    MEMORY_LIMIT = "memory_limit"
    OUTPUT_LIMIT = "output_limit"
    INFRASTRUCTURE_ERROR = "infrastructure_error"


class CompileLimits(_Frozen):
    wall_seconds: Annotated[float, Field(gt=0, le=300)] = 30.0
    cpu_seconds: Annotated[int, Field(gt=0, le=300)] = 30
    memory_mib: Annotated[int, Field(ge=64, le=8192)] = 1024
    pids: Annotated[int, Field(ge=8, le=1024)] = 64
    open_files: Annotated[int, Field(ge=16, le=4096)] = 256
    max_file_mib: Annotated[int, Field(ge=1, le=1024)] = 64
    tmpfs_mib: Annotated[int, Field(ge=16, le=4096)] = 256
    stdout_bytes: Annotated[int, Field(ge=1024)] = 64 * 1024
    stderr_bytes: Annotated[int, Field(ge=1024)] = 64 * 1024


class RunLimits(_Frozen):
    cpu_seconds: Annotated[int, Field(gt=0, le=60)] = 2
    # Host-side deadline = cpu_seconds + startup_grace_seconds (covers container start-up
    # and programs that block without using CPU, e.g. sleeping or waiting on stdin).
    startup_grace_seconds: Annotated[float, Field(ge=0.5, le=30)] = 1.0
    memory_mib: Annotated[int, Field(ge=16, le=4096)] = 256
    pids: Annotated[int, Field(ge=1, le=256)] = 16
    open_files: Annotated[int, Field(ge=8, le=1024)] = 64
    stdout_bytes: Annotated[int, Field(ge=1024)] = 64 * 1024
    stderr_bytes: Annotated[int, Field(ge=1024)] = 16 * 1024
    stdin_bytes: Annotated[int, Field(ge=1)] = 8 * 1024 * 1024

    @property
    def wall_seconds(self) -> float:
        return self.cpu_seconds + self.startup_grace_seconds


class EnvironmentInfo(_Frozen):
    """Provenance: enough to reproduce or compare runs across machines."""

    backend: str
    image: str
    image_id: str
    compiler_version: str
    container_runtime: str
    engine_version: str
    host_kernel: str


class CompileResult(_Frozen):
    status: CompileStatus
    profile: BuildProfile
    flags: tuple[str, ...]
    exit_code: int | None
    diagnostics: str  # compiler stderr, capped
    diagnostics_truncated: bool
    wall_ms: int
    detail: str = ""  # infrastructure failure description, never shown to students


class RunResult(_Frozen):
    status: RunStatus
    exit_code: int | None
    signal: int | None
    stdout: str
    stdout_truncated: bool
    stderr: str
    stderr_truncated: bool
    wall_ms: int  # host-measured, includes container start-up
    oom_killed: bool
    timed_out: bool
    detail: str = ""
