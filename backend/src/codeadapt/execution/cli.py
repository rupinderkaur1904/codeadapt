"""`codeadapt-run`: compile C++ files and run them on input files inside the sandbox.

Developer tool for exercising the execution layer by hand; prints one JSON document.

    codeadapt-run main.cpp [harness.cpp ...] --input t1.txt --input t2.txt [--sanitize]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from codeadapt.execution.backend import SandboxUnavailableError
from codeadapt.execution.docker import DockerSandbox, DockerSandboxConfig
from codeadapt.execution.models import BuildProfile, CompileStatus, SourceFile


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="codeadapt-run", description=__doc__.splitlines()[0])
    parser.add_argument("sources", nargs="+", type=Path, help="C++ source/header files")
    parser.add_argument("--input", action="append", type=Path, default=[], help="stdin file")
    parser.add_argument("--sanitize", action="store_true", help="ASan+UBSan build profile")
    return parser.parse_args(argv)


async def _main(args: argparse.Namespace) -> dict[str, object]:
    sandbox = DockerSandbox(DockerSandboxConfig.from_env())
    profile = BuildProfile.SANITIZE if args.sanitize else BuildProfile.STANDARD
    sources = [SourceFile(name=p.name, content=p.read_text("utf-8")) for p in args.sources]
    report: dict[str, object] = {"environment": (await sandbox.environment()).model_dump()}
    async with sandbox.job() as job:
        compiled = await job.compile(sources, profile)
        report["compile"] = compiled.model_dump(mode="json")
        if compiled.status is CompileStatus.OK:
            runs = [await job.run(p.read_bytes(), profile) for p in args.input]
            report["runs"] = [
                {"input": str(p), **r.model_dump(mode="json")}
                for p, r in zip(args.input, runs, strict=True)
            ]
    return report


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    try:
        report = asyncio.run(_main(args))
    except SandboxUnavailableError as exc:
        print(f"sandbox unavailable: {exc}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
