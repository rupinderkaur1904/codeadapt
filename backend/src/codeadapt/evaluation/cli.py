"""`codeadapt-eval`: run the held-out synthetic set and report methodology §6.1 metrics.

codeadapt-eval --content ../content/demo --heldout ../eval/heldout \
    --json report.json --markdown report.md
codeadapt-eval --cases ../eval/calibration --case-set calibration --method v2-candidate
codeadapt-eval --compare v1 v2-candidate --markdown comparison.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from codeadapt.content.catalogue import Catalogue
from codeadapt.diagnosis import METHODS
from codeadapt.evaluation.compare import compare, render_comparison
from codeadapt.evaluation.heldout import HeldoutCase, load_heldout
from codeadapt.evaluation.runner import (
    InvalidContentError,
    evaluate,
    evaluate_methods,
    render_markdown,
)
from codeadapt.execution.backend import SandboxUnavailableError
from codeadapt.execution.docker import DockerSandbox, DockerSandboxConfig


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codeadapt-eval", description=__doc__)
    parser.add_argument("--content", type=Path, default=Path("../content/demo"))
    parser.add_argument(
        "--heldout", "--cases", dest="heldout", type=Path, default=Path("../eval/heldout")
    )
    parser.add_argument(
        "--case-set",
        choices=("heldout", "calibration"),
        default="heldout",
        help="label for the cases; calibration results are never pooled with held-out ones",
    )
    parser.add_argument(
        "--method", choices=sorted(METHODS), default="v1", help="diagnostic parameter set"
    )
    parser.add_argument(
        "--compare",
        nargs="+",
        choices=sorted(METHODS),
        help="diagnose the same evidence with each method and write a comparison instead",
    )
    parser.add_argument("--problem", action="append", help="limit to these slugs")
    parser.add_argument("--runs", type=int, default=2, help="runs per case (reproducibility)")
    parser.add_argument("--json", type=Path, help="write the full report as JSON")
    parser.add_argument("--markdown", type=Path, help="write the report as Markdown")
    args = parser.parse_args(argv)

    catalogue = Catalogue.load(args.content)
    cases = load_heldout(args.heldout, set(args.problem) if args.problem else None)
    if not cases:
        print("no held-out cases found", file=sys.stderr)
        return 2
    sandbox = DockerSandbox(DockerSandboxConfig.from_env())
    if args.compare:
        return _compare(args, sandbox, catalogue, cases)
    try:
        report = asyncio.run(
            evaluate(sandbox, catalogue, cases, METHODS[args.method], args.runs, args.case_set)
        )
    except (SandboxUnavailableError, InvalidContentError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    markdown = render_markdown(report)
    if args.json:
        args.json.write_text(report.model_dump_json(indent=2) + "\n")
    if args.markdown:
        args.markdown.write_text(markdown)
    print(markdown)
    return 0


def _compare(
    args: argparse.Namespace,
    sandbox: DockerSandbox,
    catalogue: Catalogue,
    cases: list[HeldoutCase],
) -> int:
    if len(set(args.compare)) < 2:
        print("--compare needs at least two different methods", file=sys.stderr)
        return 2
    methods = [METHODS[name] for name in args.compare]
    try:
        reports = asyncio.run(
            evaluate_methods(sandbox, catalogue, cases, methods, args.runs, args.case_set)
        )
    except (SandboxUnavailableError, InvalidContentError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    comparison = compare(reports)
    markdown = render_comparison(comparison)
    if args.json:
        payload = {
            "comparison": comparison.model_dump(mode="json"),
            "reports": [r.model_dump(mode="json") for r in reports],
        }
        args.json.write_text(json.dumps(payload, indent=2) + "\n")
    if args.markdown:
        args.markdown.write_text(markdown)
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
