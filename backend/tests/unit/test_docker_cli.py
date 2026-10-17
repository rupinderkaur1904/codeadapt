"""ADR-020 regression coverage for the docker CLI driver, without a docker daemon.

A fake `docker` binary scripts the two failure modes seen under load:

* the attached `docker run -i` client and `docker inspect` disagree about how the
  container ended (the CI e2e run that lost its output);
* `docker kill` is slow to confirm;
* a run ends normally but its output never reaches the host (exit 0, empty stdout), which
  the end-of-output marker reveals (ADR-024);
* a run is stopped by the wall clock without reaching its CPU limit (a host stall looks
  like this), which ADR-023 re-runs once and otherwise reports as inconclusive.

This tests how `DockerSandbox` *reports* those conditions. It does not reproduce the
original CI failure, whose root cause is still unconfirmed (ADR-020).
"""

import asyncio
import os
import stat
import sys
from pathlib import Path

import pytest

from codeadapt.execution import docker as docker_module
from codeadapt.execution.backend import SandboxUnavailableError
from codeadapt.execution.docker import DockerSandbox, DockerSandboxConfig, DockerSandboxJob
from codeadapt.execution.models import BuildProfile, RunLimits, RunStatus

FAKE_DOCKER = """\
import json, os, signal, sys, time
state = os.environ["FAKE_DOCKER_STATE"]
cmd = sys.argv[1]
if cmd == "run":
    with open(os.path.join(state, "run.pid"), "w") as f:
        f.write(str(os.getpid()))
    sys.stdin.read()
    # FAKE_RUN_SECONDS is a comma-separated list: one entry per successive run.
    seq = os.environ.get("FAKE_RUN_SECONDS", "0").split(",")
    count_file = os.path.join(state, "runs")
    n = int(open(count_file).read()) if os.path.exists(count_file) else 0
    with open(count_file, "w") as f:
        f.write(str(n + 1))
    if os.path.exists(os.path.join(state, "killed")):
        os.remove(os.path.join(state, "killed"))
    time.sleep(float(seq[min(n, len(seq) - 1)]))
    sys.stdout.write(os.environ.get("FAKE_RUN_STDOUT", ""))
    if not os.environ.get("FAKE_DROP_MARKER"):  # the run script's end-of-output markers
        marker = sys.argv[sys.argv.index("-e") + 2]
        sys.stdout.write(marker)
        sys.stderr.write(marker)
    sys.exit(int(os.environ.get("FAKE_CLIENT_EXIT", "0")))
elif cmd == "inspect":
    killed = os.path.exists(os.path.join(state, "killed"))
    code = 137 if killed else int(os.environ.get("FAKE_CONTAINER_EXIT", "0"))
    print(json.dumps({"StartedAt": "2026-10-16T00:00:00Z", "ExitCode": code,
                      "OOMKilled": False}))
elif cmd == "kill":
    time.sleep(float(os.environ.get("FAKE_KILL_SECONDS", "0")))
    open(os.path.join(state, "killed"), "w").close()
    with open(os.path.join(state, "run.pid")) as f:
        os.kill(int(f.read()), signal.SIGKILL)
"""


@pytest.fixture
def fake_docker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> DockerSandbox:
    script = tmp_path / "fake_docker.py"
    script.write_text(FAKE_DOCKER)
    binary = tmp_path / "docker"
    binary.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n')
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("FAKE_DOCKER_STATE", str(state))
    return DockerSandbox(DockerSandboxConfig(docker_binary=str(binary)))


# A 1.5 s host-side deadline (1 s CPU plus 0.5 s start-up grace).
FAST = RunLimits(cpu_seconds=1, startup_grace_seconds=0.5)


def _job(sandbox: DockerSandbox) -> DockerSandboxJob:
    job = DockerSandboxJob(sandbox, "test", "codeadapt-job-test")
    job._compiled.add(BuildProfile.STANDARD)
    return job


async def test_agreeing_client_and_container_are_evidence(
    fake_docker: DockerSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_RUN_STDOUT", "42\n")
    result = await _job(fake_docker).run(b"in")
    assert result.status is RunStatus.OK
    assert result.stdout == "42\n"
    assert result.detail == ""


async def test_output_without_the_end_marker_is_an_infrastructure_error(
    fake_docker: DockerSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The CI event of 2026-10-17: exit 0 from both client and container, empty stdout.
    # The exit statuses agree, so only the missing end-of-output marker reveals it.
    monkeypatch.setenv("FAKE_DROP_MARKER", "1")
    result = await _job(fake_docker).run(b"in")
    assert result.status is RunStatus.INFRASTRUCTURE_ERROR
    assert "end-of-output marker" in result.detail


async def test_markers_are_stripped_and_output_is_unchanged(
    fake_docker: DockerSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_RUN_STDOUT", "no newline")
    result = await _job(fake_docker).run(b"in")
    assert result.status is RunStatus.OK
    assert result.stdout == "no newline"
    assert result.stderr == ""


@pytest.mark.parametrize(("client", "container"), [(0, 1), (1, 0), (0, 139)])
async def test_exit_status_disagreement_is_an_infrastructure_error(
    fake_docker: DockerSandbox, monkeypatch: pytest.MonkeyPatch, client: int, container: int
) -> None:
    # The shape of the CI failure: the client reports a clean exit with empty output while
    # the container itself exited differently (or the reverse). Neither stream is evidence.
    monkeypatch.setenv("FAKE_CLIENT_EXIT", str(client))
    monkeypatch.setenv("FAKE_CONTAINER_EXIT", str(container))
    result = await _job(fake_docker).run(b"in")
    assert result.status is RunStatus.INFRASTRUCTURE_ERROR
    assert "disagreed" in result.detail


def _runs() -> int:
    return int((Path(os.environ["FAKE_DOCKER_STATE"]) / "runs").read_text())


async def test_slow_kill_within_the_wait_still_reports_the_stop(
    fake_docker: DockerSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Before ADR-020 the kill wait was 15 s; a daemon slower than that aborted the run.
    # Scaled down: the kill takes 1.5 s and the wait allows 5 s. No stall re-run here.
    monkeypatch.setattr(docker_module, "_DOCKER_CLI_TIMEOUT", 5.0)
    monkeypatch.setattr(docker_module, "STALL_RETRY_GRACE_SECONDS", 0.5)
    monkeypatch.setenv("FAKE_RUN_SECONDS", "30")
    monkeypatch.setenv("FAKE_KILL_SECONDS", "1.5")
    result = await _job(fake_docker).run(b"in", limits=FAST)
    assert result.status is RunStatus.INCONCLUSIVE
    assert result.timed_out
    assert _runs() == 1


async def test_cpu_limit_is_a_time_limit_without_a_rerun(
    fake_docker: DockerSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_CLIENT_EXIT", "152")  # 128 + SIGXCPU
    monkeypatch.setenv("FAKE_CONTAINER_EXIT", "152")
    result = await _job(fake_docker).run(b"in", limits=FAST)
    assert result.status is RunStatus.TIME_LIMIT
    assert _runs() == 1


async def test_stalled_trivial_run_is_rerun_and_never_a_time_limit(
    fake_docker: DockerSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The CI event: a trivial program stalls past the wall deadline once. The re-run
    # (longer start-up grace, same CPU limit) completes, and its output is the evidence.
    monkeypatch.setattr(docker_module, "STALL_RETRY_GRACE_SECONDS", 2.0)
    monkeypatch.setenv("FAKE_RUN_SECONDS", "30,0")
    monkeypatch.setenv("FAKE_RUN_STDOUT", "3\n")
    result = await _job(fake_docker).run(b"in", limits=FAST)
    assert result.status is RunStatus.OK
    assert result.stdout == "3\n"
    assert "re-run after a wall-clock stop" in result.detail
    assert _runs() == 2


async def test_repeated_stall_is_inconclusive(
    fake_docker: DockerSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(docker_module, "STALL_RETRY_GRACE_SECONDS", 1.0)
    monkeypatch.setenv("FAKE_RUN_SECONDS", "30")
    result = await _job(fake_docker).run(b"in", limits=FAST)
    assert result.status is RunStatus.INCONCLUSIVE
    assert _runs() == 2


async def test_kill_slower_than_the_wait_is_reported_not_classified(
    fake_docker: DockerSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A daemon that never confirms the kill is surfaced as an unavailable sandbox, so the
    # caller retries or fails the job; it never becomes a student-facing verdict.
    monkeypatch.setattr(docker_module, "_DOCKER_CLI_TIMEOUT", 0.5)
    monkeypatch.setattr(docker_module, "STALL_RETRY_GRACE_SECONDS", 0.5)
    monkeypatch.setenv("FAKE_RUN_SECONDS", "30")
    monkeypatch.setenv("FAKE_KILL_SECONDS", "5")
    with pytest.raises(SandboxUnavailableError, match="docker kill timed out"):
        await _job(fake_docker).run(b"in", limits=FAST)
    # The client is not left running (allow the event loop a moment to reap it).
    pid = int((Path(os.environ["FAKE_DOCKER_STATE"]) / "run.pid").read_text())
    for _ in range(50):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        await asyncio.sleep(0.05)
    pytest.fail("docker run client still running after a failed kill")
