"""Compare the held-out re-run of the three changed problems with the f752a51 record.

Usage (from the repository root): python3 docs/evaluation/l20-original-s1-2026-10-26/compare_heldout.py
Keys are (method version, problem, case file); values are outcome, selected model,
candidates, classification and reproducibility. Content versions are expected to differ.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EARLIER = HERE.parent / "l20-d1-l22-2026-10-26" / "heldout"
PROBLEMS = ("lower-bound", "last-less-than", "first-true")


def cases(path):
    out = {}
    for r in json.loads(path.read_text())["reports"]:
        for p in r["problems"]:
            for c in p["cases"]:
                key = (r["method_version"], p["problem"], c["file"])
                out[key] = (
                    c["outcome"],
                    c["selected_model"],
                    tuple(c["candidates"]),
                    c["classification"],
                    c["reproducible"],
                )
    return out


before, after = {}, {}
for slug in PROBLEMS:
    before.update(cases(EARLIER / f"{slug}.json"))
    after.update(cases(HERE / "heldout" / f"{slug}.json"))
changed = sorted(k for k in set(after) & set(before) if after[k] != before[k])
print(f"cases x methods in the re-run: {len(after)}; in the f752a51 record: {len(before)}")
print(f"identical: {len(set(after) & set(before)) - len(changed)}; changed: {len(changed)}")
print(f"only in the re-run: {len(set(after) - set(before))}; only earlier: {len(set(before) - set(after))}")
for k in changed:
    print("CHANGED", k, before[k], "->", after[k])
