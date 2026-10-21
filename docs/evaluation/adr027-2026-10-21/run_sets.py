"""ADR-027 §8: v1.1 vs v1.2 on the held-out and calibration sets, case by case.

Collects evidence exactly as evaluation/runner.py::_case does (2 runs per case), records
every observation with its exclusion reason, and diagnoses the same evidence with
`METHODS["v1.1"]` and `METHODS["v1"]` (1.2). For each it records the downstream
consequences (skill observations, recommendation, feedback) from consequences.py.
The aggregate metrics come from `codeadapt-eval --compare v1.1 v1` (heldout.md,
calibration.md); this script adds the per-case detail those reports do not hold.

Run from backend/ (Docker and the sandbox image required):
    uv run python ../docs/evaluation/adr027-2026-10-21/run_sets.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from consequences import consequences

from codeadapt.content.catalogue import Catalogue
from codeadapt.content.fingerprint import fingerprint_problem
from codeadapt.content.validate import validate_fingerprints
from codeadapt.diagnosis import METHODS, DiagnosticInput
from codeadapt.evaluation.heldout import load_heldout
from codeadapt.evaluation.runner import _predictions
from codeadapt.evidence.collect import collect_evidence
from codeadapt.execution.docker import DockerSandbox, DockerSandboxConfig

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNS = 2


async def main() -> None:
    catalogue = Catalogue.load(ROOT / "content/demo")
    problems = {p.spec.slug: p.spec for p in catalogue.problems}
    sandbox = DockerSandbox(DockerSandboxConfig.from_env())
    rows = []
    for case_set in ("heldout", "calibration"):
        cases = load_heldout(ROOT / "eval" / case_set, None)
        for slug in sorted({c.problem for c in cases}):
            problem = catalogue.by_slug[slug]
            fps = await fingerprint_problem(sandbox, problem)
            if not validate_fingerprints(problem.spec, fps).ok:
                sys.exit(f"{slug}: content failed validation")
            reference = _predictions(fps, None)
            models = {k: _predictions(fps, k) for k in fps.models}
            for case in (c for c in cases if c.problem == slug):
                per: dict[str, list[dict]] = {"v1.1": [], "v1.2": []}
                observed = []
                for _ in range(RUNS):
                    evidence = await collect_evidence(sandbox, problem, case.source, reference)
                    obs = tuple(evidence.observations())
                    data = DiagnosticInput(
                        problem_version=problem.version,
                        compiled=evidence.ok,
                        observations=obs,
                        reference=reference,
                        models=models,
                    )
                    observed.append(
                        {o.test_key: [str(o.signature), o.excluded_reason] for o in obs}
                    )
                    per["v1.1"].append(
                        consequences(METHODS["v1.1"].diagnose(data), problem, problems)
                    )
                    per["v1.2"].append(consequences(METHODS["v1"].diagnose(data), problem, problems))
                rows.append(
                    {
                        "set": case_set,
                        "case": f"{slug}/{case.file}",
                        "truth": case.truth,
                        "reproducible": all(r == per[v][0] for v in per for r in per[v])
                        and all(o == observed[0] for o in observed),
                        "v1.1": per["v1.1"][0],
                        "v1.2": per["v1.2"][0],
                        "observations": observed,
                    }
                )
                print(case_set, rows[-1]["case"], rows[-1]["v1.1"]["outcome"], "->",
                      rows[-1]["v1.2"]["outcome"], flush=True)
    (HERE / "heldout-calibration.json").write_text(json.dumps(rows, indent=1) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
