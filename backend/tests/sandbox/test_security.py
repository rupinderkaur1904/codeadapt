"""Adversarial tests: each one is a guarantee listed in docs/security.md §5."""

from __future__ import annotations

import os
import subprocess
import time
import uuid
from pathlib import Path

import pytest

from codeadapt.execution import (
    CompileLimits,
    CompileStatus,
    DockerSandbox,
    DockerSandboxConfig,
    RunStatus,
    SourceFile,
)
from codeadapt.execution.docker import LABEL

from .helpers import compile_and_run


async def test_no_network_access(sandbox: DockerSandbox) -> None:
    src = r"""
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cstdio>
#include <fstream>
#include <string>
int main() {
  int s = socket(AF_INET, SOCK_STREAM, 0);
  sockaddr_in a{}; a.sin_family = AF_INET; a.sin_port = htons(80);
  inet_pton(AF_INET, "1.1.1.1", &a.sin_addr);
  int rc = s < 0 ? -1 : connect(s, (sockaddr*)&a, sizeof a);
  addrinfo* res = nullptr;
  int dns = getaddrinfo("example.com", "80", nullptr, &res);
  std::ifstream dev("/proc/net/dev"); std::string line; int ifaces = 0;
  while (std::getline(dev, line)) if (line.find(':') != std::string::npos) ++ifaces;
  std::printf("connect=%d dns=%d ifaces=%d\n", rc, dns == 0 ? 0 : 1, ifaces);
}
"""
    result = await compile_and_run(sandbox, src)
    assert result.status is RunStatus.OK, result
    # connect fails, DNS fails, and only the loopback interface exists.
    assert result.stdout.strip() == "connect=-1 dns=1 ifaces=1"


async def test_filesystem_is_read_only_everywhere(sandbox: DockerSandbox) -> None:
    src = r"""
#include <cstdio>
int main() {
  const char* paths[] = {"/work/bin/x", "/work/src/x", "/work/x", "/tmp/x", "/x", "/home/x", "/dev/shm/x", "./x"};
  int writable = 0;
  for (const char* p : paths) { if (FILE* f = std::fopen(p, "w")) { ++writable; std::printf("WRITABLE %s\n", p); std::fclose(f); } }
  std::printf("writable=%d\n", writable);
}
"""
    result = await compile_and_run(sandbox, src)
    assert result.stdout.strip().endswith("writable=0"), result.stdout


async def test_runs_unprivileged_without_capabilities(sandbox: DockerSandbox) -> None:
    src = r"""
#include <unistd.h>
#include <cstdio>
#include <fstream>
#include <string>
int main() {
  std::ifstream st("/proc/self/status"); std::string line, eff, nnp;
  while (std::getline(st, line)) {
    if (line.rfind("CapEff:", 0) == 0) eff = line.substr(7);
    if (line.rfind("NoNewPrivs:", 0) == 0) nnp = line.substr(11);
  }
  std::printf("uid=%d gid=%d cap=%s nnp=%s\n", getuid(), getgid(), eff.c_str() + eff.find_first_not_of(" \t"), nnp.c_str() + nnp.find_first_not_of(" \t"));
}
"""
    result = await compile_and_run(sandbox, src)
    assert result.stdout.strip() == "uid=65534 gid=65534 cap=0000000000000000 nnp=1"


async def test_host_environment_and_secrets_not_visible(
    sandbox: DockerSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = f"CODEADAPT_TEST_SECRET_{uuid.uuid4().hex}"
    monkeypatch.setenv("CODEADAPT_TEST_SECRET", secret)
    monkeypatch.setenv("DATABASE_URL", secret)
    src = r"""
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <sys/stat.h>
int main() {
  std::ifstream e("/proc/self/environ");
  std::string env((std::istreambuf_iterator<char>(e)), {});
  struct stat st;
  bool sock = stat("/var/run/docker.sock", &st) == 0 || stat("/run/docker.sock", &st) == 0;
  std::printf("%s\nSOCK=%d\n", env.c_str(), sock);
}
"""
    result = await compile_and_run(sandbox, src)
    assert secret not in result.stdout
    assert "SOCK=0" in result.stdout
    assert os.environ["CODEADAPT_TEST_SECRET"] == secret  # sanity: it was set on the host


async def test_compiler_cannot_include_host_files(sandbox: DockerSandbox, tmp_path: Path) -> None:
    marker = tmp_path / "host_secret.txt"
    marker.write_text("HOST_SECRET_CONTENT\n")
    src = f'#include "{marker}"\nint main() {{}}\n'
    async with sandbox.job() as job:
        compiled = await job.compile([SourceFile(name="main.cpp", content=src)])
    assert compiled.status is CompileStatus.ERROR
    assert "No such file" in compiled.diagnostics
    assert "HOST_SECRET_CONTENT" not in compiled.diagnostics


async def test_fork_bomb_is_contained(sandbox: DockerSandbox) -> None:
    src = r"""
#include <unistd.h>
#include <cstdio>
#include <csignal>
int main() {
  int ok = 0;
  for (int i = 0; i < 1000; ++i) { pid_t p = fork(); if (p == 0) { pause(); _exit(0); } if (p > 0) ++ok; }
  std::printf("forked=%d\n", ok); std::fflush(stdout);
  kill(0, SIGKILL);
}
"""
    start = time.monotonic()
    result = await compile_and_run(sandbox, src)
    assert time.monotonic() - start < 15
    forked = int(result.stdout.strip().split("=")[1])
    assert forked < 16  # --pids-limit for runs


async def test_memory_limit_kills(sandbox: DockerSandbox) -> None:
    src = r"""
#include <cstdlib>
#include <cstring>
#include <cstdio>
int main() {
  for (int i = 0; i < 64; ++i) { char* p = (char*)std::malloc(32 << 20); if (!p) return 2; std::memset(p, 1, 32 << 20); }
  std::puts("survived");
}
"""
    result = await compile_and_run(sandbox, src)
    assert result.status is RunStatus.MEMORY_LIMIT
    assert "survived" not in result.stdout


async def test_cpu_bound_infinite_loop_times_out(sandbox: DockerSandbox) -> None:
    start = time.monotonic()
    result = await compile_and_run(
        sandbox, "int main() { volatile unsigned long x = 0; for (;;) ++x; }"
    )
    elapsed = time.monotonic() - start
    assert result.status is RunStatus.TIME_LIMIT
    # Stopped by the CPU rlimit (SIGXCPU), not merely by the host-side wall deadline.
    # This requires the submission not to be PID 1 in the container (see --init).
    assert result.signal == 24
    assert not result.timed_out
    assert elapsed < 15


async def test_blocking_program_hits_wall_deadline(sandbox: DockerSandbox) -> None:
    src = "#include <unistd.h>\nint main() { for (;;) pause(); }"
    result = await compile_and_run(sandbox, src)
    assert result.status is RunStatus.TIME_LIMIT
    assert result.timed_out


async def test_output_flood_is_capped(sandbox: DockerSandbox) -> None:
    src = '#include <cstdio>\nint main() { for (;;) std::fputs("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", stdout); }'
    result = await compile_and_run(sandbox, src)
    assert result.status is RunStatus.OUTPUT_LIMIT
    assert len(result.stdout) <= 64 * 1024


async def test_background_children_die_with_the_test(sandbox: DockerSandbox) -> None:
    src = r"""
#include <unistd.h>
#include <cstdio>
int main() { if (fork() == 0) { setsid(); for (;;) sleep(1); } std::puts("parent done"); }
"""
    start = time.monotonic()
    result = await compile_and_run(sandbox, src)
    assert result.status is RunStatus.OK
    assert time.monotonic() - start < 5


async def test_runs_do_not_share_state(sandbox: DockerSandbox) -> None:
    """A run cannot leave anything behind for the next run of the same job."""
    src = r"""
#include <cstdio>
#include <sys/stat.h>
int main() {
  struct stat st; bool seen = stat("/tmp/marker", &st) == 0 || stat("/work/marker", &st) == 0;
  FILE* a = std::fopen("/tmp/marker", "w"); FILE* b = std::fopen("/work/marker", "w");
  std::printf("seen=%d wrote=%d\n", seen, a != nullptr || b != nullptr);
}
"""
    async with sandbox.job() as job:
        await job.compile([SourceFile(name="main.cpp", content=src)])
        first = await job.run(b"")
        second = await job.run(b"")
    assert first.stdout == second.stdout == "seen=0 wrote=0\n"


async def test_compile_time_resource_exhaustion_is_bounded() -> None:
    """Reading /dev/zero as a header must be stopped by compile limits, not hang."""
    sb = DockerSandbox(
        DockerSandboxConfig(
            compile_limits=CompileLimits(wall_seconds=8, cpu_seconds=6, memory_mib=256)
        )
    )
    try:
        await sb.check_available()
    except Exception as exc:
        pytest.skip(f"sandbox unavailable: {exc}")
    start = time.monotonic()
    async with sb.job() as job:
        compiled = await job.compile(
            [SourceFile(name="main.cpp", content='#include "/dev/zero"\n')]
        )
    assert time.monotonic() - start < 25
    assert compiled.status is not CompileStatus.OK


async def test_template_bomb_does_not_succeed(sandbox: DockerSandbox) -> None:
    src = """
template <int N> struct F { static constexpr long v = F<N - 1>::v + F<N - 2>::v; };
template <> struct F<1> { static constexpr long v = 1; };
template <> struct F<0> { static constexpr long v = 0; };
int main() { return F<100000>::v != 0; }
"""
    async with sandbox.job() as job:
        compiled = await job.compile([SourceFile(name="main.cpp", content=src)])
    assert compiled.status is not CompileStatus.OK


def _labelled(kind: str) -> list[str]:
    cmd = ["docker", kind, "ls", "-q", "--filter", f"label={LABEL}=1"]
    if kind == "container":
        cmd.insert(3, "-a")
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.split()


async def test_job_cleanup_after_exception(sandbox: DockerSandbox) -> None:
    before_c, before_v = set(_labelled("container")), set(_labelled("volume"))

    class BoomError(Exception):
        pass

    with pytest.raises(BoomError):
        async with sandbox.job() as job:
            await job.compile([SourceFile(name="main.cpp", content="int main(){}")])
            await job.run(b"")
            raise BoomError
    assert set(_labelled("container")) <= before_c
    assert set(_labelled("volume")) <= before_v


async def test_reaper_removes_leftovers(sandbox: DockerSandbox) -> None:
    name = f"codeadapt-leftover-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        ["docker", "volume", "create", "--label", f"{LABEL}=1", name],
        check=True,
        capture_output=True,
    )
    assert name in _labelled("volume")
    assert await sandbox.reap() >= 1
    assert name not in _labelled("volume")
