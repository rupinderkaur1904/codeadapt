"""Pure mapping from raw container outcomes to execution statuses.

Kept free of I/O so every branch is unit-tested without Docker.
"""

from __future__ import annotations

from dataclasses import dataclass

from codeadapt.execution.models import CompileStatus, RunStatus

# Shells and container runtimes report "killed by signal N" as exit status 128 + N.
_SIGNAL_EXIT_BASE = 128
SIGKILL = 9
SIGXCPU = 24


@dataclass(frozen=True, slots=True)
class RawOutcome:
    """What the sandbox backend observed about one container."""

    started: bool  # the container process actually started
    exit_code: int | None
    oom_killed: bool
    timed_out: bool  # host-side wall deadline fired
    output_overflow: bool  # a capped stream exceeded its cap
    # The `docker run` client's exit status disagreed with the container's own exit code
    # on a run that finished by itself. The attached output streams cannot then be
    # trusted (seen in CI: exit 0 with empty stdout), so the run is not evidence.
    stream_mismatch: bool = False


def signal_of(exit_code: int | None) -> int | None:
    """Signal number encoded in an exit status, if it is of the form 128 + N.

    A program can also call ``exit(137)`` itself; this is indistinguishable from SIGKILL
    at this layer and is documented as such.
    """
    if exit_code is None or exit_code <= _SIGNAL_EXIT_BASE or exit_code > _SIGNAL_EXIT_BASE + 64:
        return None
    return exit_code - _SIGNAL_EXIT_BASE


def classify_run(raw: RawOutcome) -> RunStatus:
    if not raw.started or raw.stream_mismatch:
        return RunStatus.INFRASTRUCTURE_ERROR
    # Order matters: resource-limit verdicts explain a subsequent non-zero exit.
    if raw.oom_killed:
        return RunStatus.MEMORY_LIMIT
    if raw.output_overflow:
        return RunStatus.OUTPUT_LIMIT
    # Only the CPU-time limit shows that the program itself ran too long: CPU time is
    # charged to the program's own process, so host load cannot produce it. A wall-clock
    # stop without it is what a stalled host looks like too (measured, ADR-023).
    if signal_of(raw.exit_code) == SIGXCPU:
        return RunStatus.TIME_LIMIT
    if raw.timed_out:
        return RunStatus.INCONCLUSIVE
    if raw.exit_code == 0:
        return RunStatus.OK
    if raw.exit_code is None:
        return RunStatus.INFRASTRUCTURE_ERROR
    return RunStatus.RUNTIME_ERROR


def classify_compile(raw: RawOutcome) -> CompileStatus:
    if not raw.started or raw.stream_mismatch:
        return CompileStatus.INFRASTRUCTURE_ERROR
    if raw.oom_killed:
        return CompileStatus.MEMORY_LIMIT
    if raw.output_overflow:
        return CompileStatus.OUTPUT_LIMIT
    if raw.timed_out or signal_of(raw.exit_code) in (SIGXCPU, SIGKILL):
        return CompileStatus.TIME_LIMIT
    if raw.exit_code == 0:
        return CompileStatus.OK
    if raw.exit_code is None:
        return CompileStatus.INFRASTRUCTURE_ERROR
    return CompileStatus.ERROR
