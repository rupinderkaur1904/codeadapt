"""`codeadapt-content`: validate problem content by executing it in the sandbox.

codeadapt-content validate content/demo            # every problem in a catalogue
codeadapt-content validate content/demo/lower-bound --json report.json
codeadapt-content report content/demo --out docs/content-reports
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from codeadapt.content.fingerprint import FingerprintSet, fingerprint_problem
from codeadapt.content.loader import PROBLEM_FILE, ContentError, LoadedProblem, load_catalogue
from codeadapt.content.loader import load_problem as load_one
from codeadapt.content.report import render_report
from codeadapt.content.validate import ValidationReport, validate_fingerprints
from codeadapt.execution.backend import SandboxUnavailableError
from codeadapt.execution.docker import DockerSandbox, DockerSandboxConfig


def _problems(path: Path) -> list[LoadedProblem]:
    if (path / PROBLEM_FILE).is_file():
        return [load_one(path)]
    problems = load_catalogue(path)
    if not problems:
        raise ContentError(f"{path}: no problem directories found")
    return problems


def _matrix(problem: LoadedProblem, fps: FingerprintSet) -> str:
    """Tests x programs table of observed signatures ('=' marks agreement with reference)."""
    labels = ["reference", *fps.models]
    programs = [fps.reference, *fps.models.values()]
    width = max(len(t.key) for t in problem.spec.tests)
    rows = ["  ".join([" " * width, *labels])]
    for test in problem.spec.tests:
        ref = fps.reference.tests.get(test.key)
        cells = []
        for label, fp in zip(labels, programs, strict=True):
            tf = fp.tests.get(test.key)
            if tf is None:
                cell = "n/a"
            elif tf.signature is None:
                cell = "NONDET"
            elif fp is not fps.reference and ref is not None and tf.signature == ref.signature:
                cell = "="
            else:
                cell = str(tf.signature).replace("\n", "/")
            cells.append(cell[: max(len(label), 12)].ljust(len(label)))
        rows.append("  ".join([test.key.ljust(width), *cells]))
    return "\n".join(rows)


def _print(problem: LoadedProblem, fps: FingerprintSet, report: ValidationReport) -> None:
    env = fps.environment
    print(
        f"== {problem.spec.slug}  version {problem.version[:12]}  "
        f"({env.compiler_version}, {env.container_runtime})"
    )
    print(_matrix(problem, fps))
    for m in report.models:
        tests = ", ".join(m.detecting_tests)
        print(f"  model {m.key} [{m.skill}] detected by {len(m.detecting_tests)}: {tests}")
    for p in report.pairs:
        print(f"  pair {p.a} / {p.b}: {len(p.distinguishing_tests)} distinguishing test(s)")
    for g in report.groups:
        print(f"  group {', '.join(g.tests)}: detects {', '.join(g.detected_models) or 'none'}")
    for w in report.warnings:
        print(f"  WARNING {w}")
    for lim in report.limitations:
        print(f"  LIMITATION {lim}")
    for e in report.errors:
        print(f"  ERROR {e}")
    print("  RESULT", "ok" if report.ok else "INVALID")


async def _validate(path: Path, repeats: int) -> list[dict[str, object]]:
    sandbox = DockerSandbox(DockerSandboxConfig.from_env())
    out: list[dict[str, object]] = []
    for problem in _problems(path):
        fps = await fingerprint_problem(sandbox, problem, repeats=repeats)
        report = validate_fingerprints(problem.spec, fps)
        _print(problem, fps, report)
        out.append(
            {
                "slug": problem.spec.slug,
                "report": report.model_dump(mode="json"),
                "fingerprints": fps.model_dump(mode="json"),
                "markdown": render_report(problem, fps, report),
            }
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codeadapt-content")
    sub = parser.add_subparsers(dest="command", required=True)
    val = sub.add_parser("validate", help="execute and validate problem content")
    val.add_argument("path", type=Path, help="a problem directory or a catalogue directory")
    val.add_argument("--repeats", type=int, default=2, help="runs per test (determinism check)")
    val.add_argument("--json", type=Path, help="write fingerprints and reports to this file")
    rep = sub.add_parser("report", help="validate and write a Markdown report per problem")
    rep.add_argument("path", type=Path, help="a problem directory or a catalogue directory")
    rep.add_argument("--repeats", type=int, default=2, help="runs per test (determinism check)")
    rep.add_argument("--out", type=Path, required=True, help="directory for <slug>.md reports")
    rep.set_defaults(json=None)
    args = parser.parse_args(argv)
    try:
        results = asyncio.run(_validate(args.path, args.repeats))
    except ContentError as exc:
        print(f"content error: {exc}", file=sys.stderr)
        return 1
    except SandboxUnavailableError as exc:
        print(f"sandbox unavailable: {exc}", file=sys.stderr)
        return 2
    if args.command == "report":
        args.out.mkdir(parents=True, exist_ok=True)
        for r in results:
            target = args.out / f"{r['slug']}.md"
            target.write_text(str(r["markdown"]))
            print(f"wrote {target}")
    if args.json:
        args.json.write_text(
            json.dumps([{k: v for k, v in r.items() if k != "markdown"} for r in results], indent=2)
        )
    ok = all(r["report"]["errors"] == [] for r in results)  # type: ignore[index]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
