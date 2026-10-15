"""Run a host subprocess with a deadline and hard caps on captured output."""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

_CHUNK = 64 * 1024
_KILL_GRACE_SECONDS = 10.0


@dataclass(frozen=True, slots=True)
class ProcessOutcome:
    returncode: int | None
    stdout: bytes
    stderr: bytes
    stdout_overflow: bool
    stderr_overflow: bool
    timed_out: bool
    wall_ms: int


async def _read_capped(
    stream: asyncio.StreamReader, cap: int, overflow: asyncio.Event
) -> tuple[bytes, bool]:
    """Read until EOF, keeping at most ``cap`` bytes; signal ``overflow`` past the cap."""
    buf = bytearray()
    exceeded = False
    while chunk := await stream.read(_CHUNK):
        if not exceeded:
            room = cap - len(buf)
            buf += chunk[:room]
            if len(chunk) > room:
                exceeded = True
                overflow.set()
        # After overflow keep draining so the writer is never blocked on a full pipe
        # while we wait for the kill to take effect.
    return bytes(buf), exceeded


async def run_bounded(
    argv: list[str],
    *,
    stdin: bytes,
    deadline_seconds: float,
    stdout_cap: int,
    stderr_cap: int,
    kill: Callable[[], Awaitable[None]],
    kill_on_overflow: bool = True,
    kill_grace_seconds: float = _KILL_GRACE_SECONDS,
) -> ProcessOutcome:
    """Run ``argv``, feed ``stdin``, enforce a wall-clock deadline and output caps.

    ``kill`` is invoked on deadline or (optionally) output overflow. It must terminate the
    *sandboxed workload* (e.g. ``docker kill``), not merely this client process, otherwise
    the workload could outlive us.
    """
    start = time.monotonic()
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    writer, out_stream, err_stream = proc.stdin, proc.stdout, proc.stderr
    if writer is None or out_stream is None or err_stream is None:  # pragma: no cover
        raise RuntimeError("subprocess pipes were not created")

    overflow = asyncio.Event()
    out_task = asyncio.create_task(_read_capped(out_stream, stdout_cap, overflow))
    err_task = asyncio.create_task(_read_capped(err_stream, stderr_cap, overflow))

    async def feed() -> None:
        with contextlib.suppress(BrokenPipeError, ConnectionResetError):
            writer.write(stdin)
            await writer.drain()
        with contextlib.suppress(BrokenPipeError, ConnectionResetError):
            writer.close()

    feed_task = asyncio.create_task(feed())
    wait_task = asyncio.create_task(proc.wait())
    overflow_task = asyncio.create_task(overflow.wait())

    timed_out = False
    try:
        watch = {wait_task, overflow_task} if kill_on_overflow else {wait_task}
        done, _ = await asyncio.wait(
            watch, timeout=deadline_seconds, return_when=asyncio.FIRST_COMPLETED
        )
        if wait_task not in done:
            timed_out = not done  # nothing finished → deadline; otherwise overflow
            await kill()
            try:
                await asyncio.wait_for(asyncio.shield(wait_task), kill_grace_seconds)
            except TimeoutError:
                proc.kill()  # the workload kill did not end the client; stop the client
        await wait_task
    finally:
        overflow_task.cancel()
        if not wait_task.done():  # cancelled from outside: make sure nothing survives
            await kill()
            proc.kill()
        feed_task.cancel()
        with contextlib.suppress(asyncio.CancelledError, BrokenPipeError, ConnectionResetError):
            await feed_task

    stdout, out_over = await out_task
    stderr, err_over = await err_task
    return ProcessOutcome(
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
        stdout_overflow=out_over,
        stderr_overflow=err_over,
        timed_out=timed_out,
        wall_ms=int((time.monotonic() - start) * 1000),
    )
