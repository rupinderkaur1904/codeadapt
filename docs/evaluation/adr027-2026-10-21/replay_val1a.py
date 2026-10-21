"""ADR-027 §8: v1.1 vs v1.2 on the VAL1-A programs, by replaying the recorded evidence.

Each recorded run's observations (signature and exclusion reason per test) are rebuilt
into the production `DiagnosticInput` and diagnosed with `METHODS["v1.1"]` and
`METHODS["v1"]` (1.2). Replaying v1.1 must reproduce the recorded outcome and model for
every run; the script stops if it does not. Nothing is re-executed: the method change is
isolated from execution noise. The VAL1-A results directory is read, never written.

Run from backend/: uv run python ../docs/evaluation/adr027-2026-10-21/replay_val1a.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from consequences import consequences, parse_signature

from codeadapt.content.catalogue import Catalogue
from codeadapt.diagnosis import METHODS, DiagnosticInput, Observation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VAL1A = ROOT / "docs/evaluation/val1a-2026-10-21/results"


def main() -> None:
    catalogue = Catalogue.load(ROOT / "content/demo")
    problem = catalogue.by_slug["lower-bound"]
    problems = {p.spec.slug: p.spec for p in catalogue.problems}
    env = json.loads((VAL1A / "pipeline-environment.json").read_text())
    if env["content_version"] != problem.version:
        sys.exit(f"content version changed: {problem.version} != {env['content_version']}")
    reference = {k: parse_signature(v) for k, v in env["reference"].items()}
    models = {m: {k: parse_signature(v) for k, v in p.items()} for m, p in env["models"].items()}
    cases = {c["id"]: c for c in json.loads((VAL1A / "cases.json").read_text())}
    rows = []
    for line in (VAL1A / "pipeline.jsonl").read_text().splitlines():
        rec = json.loads(line)
        per_method: dict[str, list[dict]] = {"v1.1": [], "v1.2": []}
        for run in rec["runs"]:
            data = DiagnosticInput(
                problem_version=problem.version,
                compiled=run["outcome"] != "compile_error",
                observations=tuple(
                    Observation(
                        test_key=k,
                        signature=parse_signature(v),
                        excluded_reason=run["excluded"].get(k),
                    )
                    for k, v in run["signatures"].items()
                ),
                reference=reference,
                models=models,
            )
            old = METHODS["v1.1"].diagnose(data)
            if (old.outcome.value, old.selected_model) != (run["outcome"], run["selected_model"]):
                sys.exit(f"v1.1 replay differs from the record for {rec['program']}")
            new = METHODS["v1"].diagnose(data)
            per_method["v1.1"].append(consequences(old, problem, problems))
            per_method["v1.2"].append(consequences(new, problem, problems))
        for name, results in per_method.items():
            if any(r != results[0] for r in results):
                sys.exit(f"{name} differs between the recorded runs of {rec['program']}")
        case = cases.get(rec["program"], {})
        rows.append(
            {
                "set": "val1a",
                "case": rec["program"],
                "category": case.get("category", "original"),
                "truth_strict": case.get("label_strict", "correct"),
                "truth_lenient": case.get("label_lenient", "correct"),
                "v1.1": per_method["v1.1"][0],
                "v1.2": per_method["v1.2"][0],
            }
        )
    (HERE / "val1a.json").write_text(json.dumps(rows, indent=1) + "\n")
    print(f"{len(rows)} programs replayed; v1.1 reproduced the record for every run")


if __name__ == "__main__":
    main()
