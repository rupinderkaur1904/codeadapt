"""VAL1-A2: run the originals and every kept mutant through the production evidence and
diagnosis path (PLAN.md §1), 2 runs each, exactly as evaluation/runner.py::_case does.
Records every observation with its exclusion reason and diagnoses the same evidence with
method 1.2 (primary) and 1.1 (secondary). Changes no production code.

Run from backend/ (Docker and the sandbox image required):
    uv run python ../docs/evaluation/val1a2-2026-10-22/run_audit.py

The 2 runs per program (PLAN.md §1) are done as two passes over all three problems, so a
complete first-run picture exists before the reproducibility runs (execution order only):
    uv run python ../docs/evaluation/val1a2-2026-10-22/run_audit.py 1   -> results/<problem>.jsonl
    uv run python ../docs/evaluation/val1a2-2026-10-22/run_audit.py 2   -> results/<problem>.run2.jsonl
One line per program; a restart skips recorded programs.
Stops (PLAN.md §9) on a content-version change (X2), a failed content validation (X2), or
an original that does not pass its suite (X1).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from codeadapt.content.catalogue import Catalogue
from codeadapt.content.fingerprint import fingerprint_problem
from codeadapt.content.validate import validate_fingerprints
from codeadapt.diagnosis import METHODS, DiagnosticInput
from codeadapt.evaluation.runner import _predictions
from codeadapt.evidence.collect import collect_evidence
from codeadapt.execution.docker import DockerSandbox, DockerSandboxConfig

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PASS = int(sys.argv[1]) if len(sys.argv) > 1 else 1
BATCH = 6
FROZEN = {
    "count-occurrences": "d1b043c04574",
    "last-less-than": "3d52811ae14b",
    "first-true": "b69c5efa3b39",
}


def summary(d) -> dict:  # type: ignore[no-untyped-def]
    return {
        "outcome": d.outcome.value,
        "selected_model": d.selected_model,
        "candidates": list(d.candidates),
        "support": d.support,
        "support_behaviours": d.rationale.get("support_behaviours"),
        "evidence_strength": d.rationale.get("evidence_strength"),
        "supporting_tests": d.rationale.get("supporting_tests", []),
        "failing_tests": d.rationale.get("failing_tests", []),
        "timed_out_tests": d.rationale.get("timed_out_tests", []),
        "consistent_models": d.rationale.get("consistent_models", []),
    }


async def one(sandbox, problem, name, source, reference, models) -> dict:  # type: ignore[no-untyped-def]
    evidence = await collect_evidence(sandbox, problem, source, reference)
    observations = evidence.observations()
    data = DiagnosticInput(
        problem_version=problem.version,
        compiled=evidence.ok,
        observations=tuple(observations),
        reference=reference,
        models=models,
    )
    run = {
        "compiled": evidence.ok,
        "observations": {o.test_key: [str(o.signature), o.excluded_reason] for o in observations},
        "v1.2": summary(METHODS["v1"].diagnose(data)),
        "v1.1": summary(METHODS["v1.1"].diagnose(data)),
    }
    return {"program": name, "runs": [run]}


async def audit(sandbox: DockerSandbox, catalogue: Catalogue, slug: str) -> None:
    problem = catalogue.by_slug[slug]
    if not problem.version.startswith(FROZEN[slug]):
        sys.exit(f"X2: {slug} content version changed: {problem.version}")
    fps = await fingerprint_problem(sandbox, problem)
    validation = validate_fingerprints(problem.spec, fps)
    if not validation.ok:
        sys.exit(f"X2: {slug} content failed validation: {validation.errors}")
    reference = _predictions(fps, None)
    models = {k: _predictions(fps, k) for k in fps.models}
    env = await sandbox.environment()
    (HERE / "results").mkdir(exist_ok=True)
    header = HERE / f"results/{slug}-environment.json"
    if PASS == 2:
        old = json.loads(header.read_text())
        if old["content_version"] != problem.version or old["compiler"] != env.compiler_version:
            sys.exit(f"X2: {slug} content or environment changed between passes")
    header.write_text(
        json.dumps(
            {
                "methods": [f"fingerprint_consistency {METHODS[m].version}" for m in ("v1", "v1.1")],
                "content_version": problem.version,
                "compiler": env.compiler_version,
                "runtime": env.container_runtime,
                "image": env.image,
                "runs_per_program": 2,
                "passes": "run 1 in <problem>.jsonl, run 2 in <problem>.run2.jsonl",
                "reference": {k: str(v) for k, v in reference.items()},
                "models": {m: {k: str(v) for k, v in p.items()} for m, p in models.items()},
            },
            indent=1,
        )
        + "\n"
    )
    base = ROOT / "eval/mutation" / slug
    programs = {f"original:{p.stem}": p for p in sorted((base / "originals").glob("*.cpp"))}
    programs |= {p.stem: p for p in sorted((base / "mutants").glob("*.cpp"))}
    out = HERE / (f"results/{slug}.jsonl" if PASS == 1 else f"results/{slug}.run2.jsonl")
    done = set()
    if out.exists():
        done = {json.loads(line)["program"] for line in out.read_text().splitlines() if line}
    todo = [(n, p) for n, p in programs.items() if n not in done]
    print(f"{slug}: {len(programs)} programs, {len(done)} recorded, {len(todo)} to run", flush=True)
    for i in range(0, len(todo), BATCH):
        batch = todo[i : i + BATCH]
        rows = await asyncio.gather(
            *(one(sandbox, problem, n, p.read_text(), reference, models) for n, p in batch)
        )
        for row in rows:
            if row["program"].startswith("original:"):
                bad = [r["v1.2"]["outcome"] for r in row["runs"] if r["v1.2"]["outcome"] != "no_failure_observed"]
                if bad:
                    sys.exit(f"X1: {slug} {row['program']} gave {bad}")
        with out.open("a") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        print(f"{slug}: {min(i + BATCH, len(todo))}/{len(todo)}", flush=True)
    rows = [json.loads(line) for line in out.read_text().splitlines() if line]
    errors = sum(any(r["v1.2"]["outcome"] == "execution_error" for r in row["runs"]) for row in rows)
    if errors * 10 > len(rows):
        sys.exit(f"X3: {slug} {errors}/{len(rows)} programs ended in execution_error")


async def main() -> None:
    catalogue = Catalogue.load(ROOT / "content/demo")
    sandbox = DockerSandbox(DockerSandboxConfig.from_env())
    for slug in FROZEN:
        await audit(sandbox, catalogue, slug)


if __name__ == "__main__":
    asyncio.run(main())
