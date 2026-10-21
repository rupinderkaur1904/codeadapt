"""VAL1-A behaviour ground truth (PLAN.md §5): each mutant against the reference on a fixed
random-input set, compiled natively with g++ -O1 (analysis only, outside the sandbox).

Run from the repository root:  python3 docs/evaluation/val1a-2026-10-21/equivalence.py
Writes docs/evaluation/val1a-2026-10-21/results/equivalence.json.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / "eval/mutation/lower-bound"
REFERENCE = ROOT / "content/demo/lower-bound/reference.cpp"


def build(src: Path, out: Path) -> bool:
    cmd = ["g++", "-O1", "-std=c++17", str(HERE / "equivalence_driver.cpp"), str(src), "-o", str(out)]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def main() -> None:
    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        assert build(REFERENCE, t / "ref"), "reference must compile"
        (t / "ref.txt").write_text(subprocess.run([t / "ref", "dump"], capture_output=True, text=True, check=True).stdout)
        programs = {f"original:{p.stem}": p for p in sorted((BASE / "originals").glob("*.cpp"))}
        programs |= {p.stem: p for p in sorted((BASE / "mutants").glob("*.cpp"))}
        for name, src in programs.items():
            if not build(src, t / "bin"):
                results[name] = {"native": "compile_error"}
                continue
            out = subprocess.run([t / "bin", "check", t / "ref.txt"], capture_output=True, text=True, timeout=900).stdout.split()
            if out and out[0] == "EQUIVALENT":
                results[name] = {"native": "equivalent", "inputs": int(out[1])}
            elif out and out[0] == "DIFF":
                results[name] = {"native": "non_equivalent", "first_diff_input": int(out[1]), "expected": out[2], "got": out[3]}
            else:
                results[name] = {"native": "check_failed"}
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results/equivalence.json").write_text(json.dumps(results, indent=1, sort_keys=True) + "\n")
    counts: dict[str, int] = {}
    for r in results.values():
        counts[r["native"]] = counts.get(r["native"], 0) + 1
    print(counts)


if __name__ == "__main__":
    main()
