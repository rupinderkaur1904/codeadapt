"""VAL1-A: run the originals and every kept mutant through the production evidence and
diagnosis path (PLAN.md §1), 2 runs each, exactly as evaluation/runner.py::_case does, and
record the extra fields the audit needs. Changes no production code.

Run from backend/ (Docker and the sandbox image required):
    uv run python ../docs/evaluation/val1a-2026-10-21/run_audit.py

Writes ../docs/evaluation/val1a-2026-10-21/results/pipeline.jsonl, one line per program;
a restart skips programs already recorded.
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
BASE = ROOT / "eval/mutation/lower-bound"
OUT = HERE / "results/pipeline.jsonl"
RUNS = 2
BATCH = 6
FROZEN_VERSION_PREFIX = "871602bc2bba"


async def one(sandbox, problem, name, source, reference, models, method) -> dict:
    runs = []
    for _ in range(RUNS):
        evidence = await collect_evidence(sandbox, problem, source, reference)
        observations = evidence.observations()
        data = DiagnosticInput(
            problem_version=problem.version,
            compiled=evidence.ok,
            observations=tuple(observations),
            reference=reference,
            models=models,
        )
        d = method.diagnose(data)
        runs.append(
            {
                "outcome": d.outcome.value,
                "selected_model": d.selected_model,
                "candidates": list(d.candidates),
                "support": d.support,
                "support_behaviours": d.rationale.get("support_behaviours"),
                "evidence_strength": d.rationale.get("evidence_strength"),
                "excluded": d.rationale.get("excluded", {}),
                "failing_tests": d.rationale.get("failing_tests", []),
                "nearest_models": d.rationale.get("nearest_models"),
                "signatures": {o.test_key: str(o.signature) for o in observations},
            }
        )
    return {"program": name, "runs": runs}


async def main() -> None:
    catalogue = Catalogue.load(ROOT / "content/demo")
    problem = catalogue.by_slug["lower-bound"]
    if not problem.version.startswith(FROZEN_VERSION_PREFIX):
        sys.exit(f"content version changed: {problem.version}")
    method = METHODS["v1"]
    sandbox = DockerSandbox(DockerSandboxConfig.from_env())
    fps = await fingerprint_problem(sandbox, problem)
    validation = validate_fingerprints(problem.spec, fps)
    if not validation.ok:
        sys.exit(f"content failed validation: {validation.errors}")
    reference = _predictions(fps, None)
    models = {k: _predictions(fps, k) for k in fps.models}
    env = await sandbox.environment()
    header = HERE / "results/pipeline-environment.json"
    header.parent.mkdir(exist_ok=True)
    header.write_text(
        json.dumps(
            {
                "method": f"{method.name} {method.version}",
                "content_version": problem.version,
                "compiler": env.compiler_version,
                "runtime": env.container_runtime,
                "image": env.image,
                "runs_per_program": RUNS,
                "reference": {k: str(v) for k, v in reference.items()},
                "models": {m: {k: str(v) for k, v in p.items()} for m, p in models.items()},
            },
            indent=1,
        )
        + "\n"
    )
    programs = {f"original:{p.stem}": p for p in sorted((BASE / "originals").glob("*.cpp"))}
    programs |= {p.stem: p for p in sorted((BASE / "mutants").glob("*.cpp"))}
    done = set()
    if OUT.exists():
        done = {json.loads(line)["program"] for line in OUT.read_text().splitlines() if line}
    todo = [(n, p) for n, p in programs.items() if n not in done]
    print(f"{len(programs)} programs, {len(done)} already recorded, {len(todo)} to run", flush=True)
    for i in range(0, len(todo), BATCH):
        batch = todo[i : i + BATCH]
        rows = await asyncio.gather(
            *(one(sandbox, problem, n, p.read_text(), reference, models, method) for n, p in batch)
        )
        with OUT.open("a") as f:
            for row in rows:
                f.write(json.dumps(row, sort_keys=True) + "\n")
        print(f"{i + len(batch)}/{len(todo)}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
