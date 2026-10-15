"""Functional behaviour of the sandbox: compile, run, classify, provenance."""

from __future__ import annotations

import asyncio

import pytest

from codeadapt.execution import (
    BuildProfile,
    CompileStatus,
    DockerSandbox,
    RunLimits,
    RunStatus,
    SourceFile,
)

from .helpers import compile_and_run

SUM = """
#include <iostream>
int main() { long a, b; std::cin >> a >> b; std::cout << a + b << "\\n"; }
"""


async def test_environment_records_provenance(sandbox: DockerSandbox) -> None:
    env = await sandbox.environment()
    assert env.backend == "docker"
    assert env.image_id.startswith("sha256:")
    assert "14.2" in env.compiler_version
    assert env.container_runtime


async def test_compile_and_run_many_inputs(sandbox: DockerSandbox) -> None:
    async with sandbox.job() as job:
        compiled = await job.compile([SourceFile(name="main.cpp", content=SUM)])
        assert compiled.status is CompileStatus.OK
        assert "-std=c++20" in compiled.flags
        results = [await job.run(f"{i} {i}".encode()) for i in range(3)]
    assert [r.stdout for r in results] == ["0\n", "2\n", "4\n"]
    assert all(r.status is RunStatus.OK and r.exit_code == 0 for r in results)


async def test_harness_and_solution_are_linked(sandbox: DockerSandbox) -> None:
    solution = "int twice(int x) { return 2 * x; }\n"
    harness = (
        "#include <iostream>\nint twice(int);\n"
        "int main() { int x; std::cin >> x; std::cout << twice(x) << '\\n'; }\n"
    )
    async with sandbox.job() as job:
        compiled = await job.compile(
            [
                SourceFile(name="solution.cpp", content=solution),
                SourceFile(name="harness.cpp", content=harness),
            ]
        )
        assert compiled.status is CompileStatus.OK, compiled.diagnostics
        assert (await job.run(b"21")).stdout == "42\n"


async def test_compile_error_is_reported(sandbox: DockerSandbox) -> None:
    async with sandbox.job() as job:
        compiled = await job.compile(
            [SourceFile(name="main.cpp", content="int main() { return x; }")]
        )
    assert compiled.status is CompileStatus.ERROR
    assert "x" in compiled.diagnostics
    assert "not declared" in compiled.diagnostics


async def test_runtime_error_signal(sandbox: DockerSandbox) -> None:
    result = await compile_and_run(sandbox, "int main() { volatile int* p = nullptr; return *p; }")
    assert result.status is RunStatus.RUNTIME_ERROR
    assert result.signal == 11


async def test_abort_reports_sigabrt(sandbox: DockerSandbox) -> None:
    result = await compile_and_run(sandbox, "#include <cstdlib>\nint main() { std::abort(); }")
    assert result.status is RunStatus.RUNTIME_ERROR
    assert result.signal == 6


async def test_nonzero_exit_is_runtime_error(sandbox: DockerSandbox) -> None:
    result = await compile_and_run(sandbox, "int main() { return 3; }")
    assert result.status is RunStatus.RUNTIME_ERROR
    assert result.exit_code == 3
    assert result.signal is None


async def test_sanitizer_profile_detects_out_of_bounds(sandbox: DockerSandbox) -> None:
    src = """
#include <vector>
#include <iostream>
int main() { std::vector<int> v(4); int i; std::cin >> i; std::cout << v.data()[i] << "\\n"; }
"""
    result = await compile_and_run(sandbox, src, b"4", profile=BuildProfile.SANITIZE)
    assert result.status is RunStatus.RUNTIME_ERROR
    assert "AddressSanitizer" in result.stderr


async def test_large_stdin_round_trip(sandbox: DockerSandbox) -> None:
    src = """
#include <iostream>
#include <string>
int main() { std::string s; long n = 0; while (std::cin >> s) n += s.size(); std::cout << n << "\\n"; }
"""
    payload = b"abcd " * 200_000  # 1 MB
    result = await compile_and_run(sandbox, src, payload)
    assert result.stdout == "800000\n"


async def test_run_before_compile_is_rejected(sandbox: DockerSandbox) -> None:
    async with sandbox.job() as job:
        with pytest.raises(RuntimeError, match="not been compiled"):
            await job.run(b"")


async def test_concurrent_jobs_are_independent(sandbox: DockerSandbox) -> None:
    async def one(k: int) -> str:
        src = f'#include <iostream>\nint main() {{ std::cout << {k} << "\\n"; }}\n'
        return (await compile_and_run(sandbox, src)).stdout

    outputs = await asyncio.gather(*(one(k) for k in range(4)))
    assert outputs == ["0\n", "1\n", "2\n", "3\n"]


async def test_custom_run_limits_apply(sandbox: DockerSandbox) -> None:
    src = "#include <thread>\n#include <chrono>\nint main(){ std::this_thread::sleep_for(std::chrono::seconds(3)); }"
    result = await compile_and_run(
        sandbox, src, limits=RunLimits(cpu_seconds=1, startup_grace_seconds=1.0)
    )
    assert result.status is RunStatus.TIME_LIMIT
