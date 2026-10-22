"""VAL1-A2 behavioural labels (PLAN.md §4-5), computed natively before any pipeline run.

For each problem: dump the reference's and every error model's outputs on the behaviour
set, then label each mutant `reference`, `model:<key>` (all matching models listed) or
`none`. Also labels the VAL1-A lower-bound mutants, for comparability; nothing in VAL1-A's
directories is written.

Run from the repository root:  python3 docs/evaluation/val1a2-2026-10-22/label.py [problem ...]
Writes eval/mutation/<problem>/behaviour_labels.json for the three problems and
docs/evaluation/val1a2-2026-10-22/results/lower-bound-behaviour-labels.json.
"""

from __future__ import annotations

import json
import sys
import subprocess
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DRIVER = HERE / "behaviour_driver.cpp"
DEFINES = {
    "count-occurrences": "P_COUNT",
    "last-less-than": "P_LAST",
    "first-true": "P_FIRST_TRUE",
    "lower-bound": "P_LOWER_BOUND",
}


def build(src: Path, define: str, out: Path) -> bool:
    cmd = ["g++", "-O1", "-std=c++17", f"-D{define}", str(DRIVER), str(src), "-o", str(out)]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def label_problem(problem: str, tmp: Path) -> dict[str, dict]:
    define = DEFINES[problem]
    content = ROOT / "content/demo" / problem
    spec = tomllib.loads((content / "problem.toml").read_text())
    targets = {"reference": content / "reference.cpp"}
    targets |= {f"model:{m['key']}": content / m["file"] for m in spec["error_models"]}
    dumps = []
    for name, src in targets.items():
        exe = tmp / f"{problem}-{name.replace(':', '_')}"
        if not build(src, define, exe):
            raise SystemExit(f"{problem}: {name} does not compile natively")
        dump = exe.with_suffix(".txt")
        dump.write_text(subprocess.run([exe, "dump"], capture_output=True, text=True, check=True).stdout)
        dumps.append((name, dump))
    base = ROOT / "eval/mutation" / problem
    mutants = sorted((base / "mutants").glob("*.cpp"))
    originals = sorted((base / "originals").glob("*.cpp"))

    def one(src: Path) -> tuple[str, dict]:
        key = src.stem if src.parent.name == "mutants" else f"original:{src.stem}"
        exe = tmp / f"{problem}-bin-{key.replace(':', '_')}"
        if not build(src, define, exe):
            return key, {"label": "compile_error", "matches": []}
        out = subprocess.run(
            [exe, "match", *[str(d) for _, d in dumps]],
            capture_output=True,
            text=True,
            timeout=3600,
        ).stdout.split("\n")
        matches = [name for (name, _), line in zip(dumps, out, strict=False) if line == "MATCH"]
        first_diff = {
            name: int(line.split()[1])
            for (name, _), line in zip(dumps, out, strict=False)
            if line.startswith("DIFF")
        }
        if "reference" in matches:
            label = "reference"
        elif matches:
            label = "model:" + ",".join(sorted(m.split(":", 1)[1] for m in matches))
        else:
            label = "none"
        return key, {"label": label, "matches": matches, "first_diff_vs_reference": first_diff.get("reference")}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = dict(pool.map(one, originals + mutants))
    ref_text = dumps[0][1].read_text()
    same = [name for name, d in dumps[1:] if d.read_text() == ref_text]
    if same:
        raise SystemExit(f"{problem}: error models equivalent to the reference: {same}")
    return results


def main() -> None:
    (HERE / "results").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for problem in sys.argv[1:] or DEFINES:
            labels = label_problem(problem, tmp)
            bad = [k for k, v in labels.items() if k.startswith("original:") and v["label"] != "reference"]
            if bad:
                raise SystemExit(f"{problem}: originals not equivalent to the reference: {bad}")
            out = (
                HERE / "results/lower-bound-behaviour-labels.json"
                if problem == "lower-bound"
                else ROOT / "eval/mutation" / problem / "behaviour_labels.json"
            )
            out.write_text(json.dumps(labels, indent=1, sort_keys=True) + "\n")
            counts: dict[str, int] = {}
            for v in labels.values():
                k = v["label"] if not v["label"].startswith("model:") else "model"
                counts[k] = counts.get(k, 0) + 1
            print(problem, counts, flush=True)


if __name__ == "__main__":
    main()
