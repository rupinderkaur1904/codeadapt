"""Lost-output probe (ADR-020, ADR-024): run many short, deterministic sandbox runs and
count the runs whose output did not reach the host.

Diagnostic tooling only. It drives the production `DockerSandbox` (variant `production`)
and a few variants that each change one thing in how the container is started, so that a
difference in loss rate points at the part of the stream path responsible:

  production    exactly the runner's command line (`docker run -i`, --init, --log-driver none)
  json-log      same, with the default json-file log driver instead of `none`
  no-init       same, without --init (tini)
  create-start  `docker create` + `docker start -a -i` instead of `docker run -i`

For every lost run it records which streams lost their end-of-output marker, the exit status
seen by the client and by the daemon, and the wall time. It never touches content, methods
or the database. Usage (from backend/):

  uv run python ../eval/infra/lost-output/probe.py --runs 2000 --concurrency 8 \
      --variants production,json-log --json out.json
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import json
import platform
import subprocess
import time
import uuid
from typing import Any

from codeadapt.execution import DockerSandbox, DockerSandboxConfig
from codeadapt.execution.docker import DockerSandboxJob
from codeadapt.execution.models import RunStatus, SourceFile

# Reads one integer (or nothing) and prints a deterministic answer, like the demo harnesses.
SOURCE = (
    "#include <cstdio>\n"
    'int main() { long n = 0; if (std::scanf("%ld", &n) != 1) n = 0;\n'
    '  std::printf("%ld\\n", n * 2); std::fprintf(stderr, "e"); return 0; }\n'
)


class VariantSandbox(DockerSandbox):
    def __init__(self, variant: str, config: DockerSandboxConfig) -> None:
        super().__init__(config)
        self.variant = variant

    def _hardening(self, **kw: int) -> list[str]:  # type: ignore[override]
        args = super()._hardening(**kw)
        if self.variant == "json-log":
            i = args.index("--log-driver")
            args[i + 1] = "json-file"
        if self.variant == "no-init":
            args.remove("--init")
        return args


def use_create_start() -> None:
    """Start runs with `docker create` + `docker start -a -i` instead of `docker run -i`."""
    import codeadapt.execution.docker as production

    original = production.run_bounded

    async def create_then_start(argv: list[str], **kw: Any) -> Any:
        binary, _run, _i, _flag, name, *docker_args = argv
        created = subprocess.run(
            [binary, "create", "-i", "--name", name, *docker_args],
            capture_output=True,
            text=True,
            check=False,
        )
        if created.returncode != 0:
            raise RuntimeError(created.stderr)
        return await original([binary, "start", "-a", "-i", name], **kw)

    production.run_bounded = create_then_start  # type: ignore[assignment]


async def probe(variant: str, runs: int, concurrency: int) -> dict[str, Any]:
    if variant == "create-start":
        use_create_start()
    sandbox = VariantSandbox(variant, DockerSandboxConfig(max_concurrency=concurrency))
    counts: collections.Counter[str] = collections.Counter()
    lost: list[dict[str, Any]] = []
    start = time.monotonic()
    async with sandbox.job() as job:
        compiled = await job.compile([SourceFile(name="main.cpp", content=SOURCE)])
        if compiled.status.value != "ok":
            raise RuntimeError(compiled.diagnostics)

        async def one(i: int, job: DockerSandboxJob = job) -> None:
            stdin = b"" if i % 3 == 0 else f"{i}\n".encode()
            expected = "0\n" if i % 3 == 0 else f"{2 * i}\n"
            # _run_once: no stall re-run, so every event is counted as it happened.
            res = await job._run_once(stdin, compiled.profile, sandbox.config.run_limits)
            key = res.status.value
            if res.status is RunStatus.OK and (res.stdout != expected or res.stderr != "e"):
                key = "wrong_output"  # lost output the marker did not catch
            if key in ("wrong_output", "infrastructure_error"):
                lost.append(
                    {
                        "i": i,
                        "stdin_empty": not stdin,
                        "status": res.status.value,
                        "detail": res.detail,
                        "stdout": res.stdout[:80],
                        "stderr": res.stderr[:80],
                        "exit_code": res.exit_code,
                        "wall_ms": res.wall_ms,
                    }
                )
            counts[key] += 1

        await asyncio.gather(*(one(i) for i in range(runs)))
    return {
        "variant": variant,
        "runs": runs,
        "concurrency": concurrency,
        "seconds": round(time.monotonic() - start, 1),
        "counts": dict(counts),
        "lost": lost,
    }


def environment() -> dict[str, str]:
    def sh(*cmd: str) -> str:
        return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout.strip()

    return {
        "kernel": platform.release(),
        "docker": sh("docker", "version", "--format", "{{.Server.Version}}"),
        "containerd": sh("docker", "info", "--format", "{{.ContainerdCommit.ID}}"),
        "runc": sh("docker", "info", "--format", "{{.RuncCommit.ID}}"),
        "cgroup": sh("docker", "info", "--format", "{{.CgroupVersion}}"),
        "cpus": sh("nproc"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--runs", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--variants", default="production")
    parser.add_argument("--json")
    args = parser.parse_args()
    report: dict[str, Any] = {
        "id": uuid.uuid4().hex[:8],
        "environment": environment(),
        "results": [],
    }
    for variant in args.variants.split(","):
        result = asyncio.run(probe(variant, args.runs, args.concurrency))
        report["results"].append(result)
        print(variant, result["counts"], f"{result['seconds']} s", flush=True)
        for entry in result["lost"][:10]:
            print("   ", entry, flush=True)
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(report, fh, indent=2)


if __name__ == "__main__":
    main()
