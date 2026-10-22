"""VAL1-A2 native symptom counts (PLAN.md §7, coarse-signature cross-check).

Runs every original and kept mutant of the three problems natively on the behaviour set
(`behaviour_driver.cpp dump`) and counts the inputs ending in TLE or CRASH. Used only to
cross-check the pipeline's `time_limit`, `runtime_error` and `memory_limit` signatures;
it decides no label. Run after run_audit.py has finished, never alongside the sandbox
(it competes for CPU).

Run from the repository root:  python3 docs/evaluation/val1a2-2026-10-22/native_symptoms.py
Writes docs/evaluation/val1a2-2026-10-22/results/native-symptoms.json.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from label import DEFINES, ROOT, build

HERE = Path(__file__).resolve().parent
PROBLEMS = ("count-occurrences", "last-less-than", "first-true")


def main() -> None:
    result: dict[str, dict[str, dict]] = {}
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for problem in PROBLEMS:
            base = ROOT / "eval/mutation" / problem
            sources = sorted((base / "originals").glob("*.cpp")) + sorted((base / "mutants").glob("*.cpp"))

            def one(src: Path, problem: str = problem) -> tuple[str, dict]:
                key = src.stem if src.parent.name == "mutants" else f"original:{src.stem}"
                exe = tmp / f"{problem}-{key.replace(':', '_')}"
                if not build(src, DEFINES[problem], exe):
                    return key, {"compiled": False}
                out = subprocess.run([exe, "dump"], capture_output=True, text=True).stdout.split()
                return key, {
                    "compiled": True,
                    "inputs": len(out),
                    "tle": out.count("TLE"),
                    "crash": out.count("CRASH"),
                }

            with ThreadPoolExecutor(max_workers=4) as pool:
                result[problem] = dict(pool.map(one, sources))
            print(problem, sum(v.get("tle", 0) > 0 for v in result[problem].values()), "with TLE,",
                  sum(v.get("crash", 0) > 0 for v in result[problem].values()), "with CRASH", flush=True)
    (HERE / "results/native-symptoms.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
