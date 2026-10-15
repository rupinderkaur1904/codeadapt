import sys

from codeadapt.execution.process import run_bounded

PY = sys.executable


async def _noop() -> None:
    return None


async def test_captures_output_and_feeds_stdin() -> None:
    out = await run_bounded(
        [PY, "-c", "import sys; d=sys.stdin.read(); print(d.upper()); print('e', file=sys.stderr)"],
        stdin=b"hello",
        deadline_seconds=10,
        stdout_cap=1024,
        stderr_cap=1024,
        kill=_noop,
    )
    assert out.returncode == 0
    assert out.stdout == b"HELLO\n"
    assert out.stderr == b"e\n"
    assert not (out.timed_out)
    assert not (out.stdout_overflow)
    assert not (out.stderr_overflow)


async def test_deadline_invokes_kill_and_reports_timeout() -> None:
    calls: list[str] = []

    async def kill() -> None:
        calls.append("kill")

    out = await run_bounded(
        [PY, "-c", "import time; time.sleep(30)"],
        stdin=b"",
        deadline_seconds=0.5,
        stdout_cap=1024,
        stderr_cap=1024,
        kill=kill,
        kill_grace_seconds=0.5,  # kill() is a no-op here, so the client fallback must fire
    )
    assert calls == ["kill"]
    assert out.timed_out
    assert out.wall_ms < 5000


async def test_output_overflow_is_capped_and_stops_process() -> None:
    out = await run_bounded(
        [PY, "-c", "import sys\nwhile True: sys.stdout.write('x' * 65536)"],
        stdin=b"",
        deadline_seconds=10,
        stdout_cap=4096,
        stderr_cap=1024,
        kill=_noop,
        kill_grace_seconds=0.5,
    )
    assert out.stdout_overflow
    assert not out.timed_out
    assert len(out.stdout) == 4096


async def test_overflow_without_kill_truncates_but_waits() -> None:
    out = await run_bounded(
        [PY, "-c", "import sys; sys.stderr.write('y' * 100000)"],
        stdin=b"",
        deadline_seconds=10,
        stdout_cap=1024,
        stderr_cap=1024,
        kill=_noop,
        kill_on_overflow=False,
    )
    assert out.returncode == 0
    assert out.stderr_overflow
    assert len(out.stderr) == 1024


async def test_unread_stdin_does_not_block() -> None:
    out = await run_bounded(
        [PY, "-c", "print('ok')"],
        stdin=b"z" * (4 * 1024 * 1024),
        deadline_seconds=10,
        stdout_cap=1024,
        stderr_cap=1024,
        kill=_noop,
    )
    assert out.returncode == 0
    assert out.stdout == b"ok\n"
