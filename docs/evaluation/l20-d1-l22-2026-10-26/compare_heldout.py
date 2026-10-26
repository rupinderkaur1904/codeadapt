"""Compare the held-out re-run with the latest earlier record of each case (from docs/evaluation).

Usage (from the repository root): python3 docs/evaluation/l20-d1-l22-2026-10-26/compare_heldout.py
Keys are (method version, problem, case file); values are outcome, selected model,
candidates, classification and reproducibility. Content versions are expected to differ.
"""

import json
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
# Earlier records, oldest first; a later record replaces an earlier one for the same key.
EARLIER = [
    "adr030-2026-10-23/heldout.json",
    "ce1.2-2026-10-24/heldout.json",
    *sorted(str(p.relative_to(EVAL)) for p in (EVAL / "ce2-2026-10-24").glob("*.json")),
    *sorted(
        str(p.relative_to(EVAL))
        for p in (EVAL / "expansion-2026-10-25").glob("*.json")
        if p.stem != "second-largest"
    ),
    "adr032-2026-10-25/min-capacity.json",
]


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


before = {}
source = {}
for rel in EARLIER:
    for k, v in cases(EVAL / rel).items():
        before[k], source[k] = v, rel
after = {}
for p in sorted((HERE / "heldout").glob("*.json")):
    after.update(cases(p))

missing = sorted(set(after) - set(before))
gone = sorted(set(before) - set(after))
changed = sorted(k for k in set(after) & set(before) if after[k] != before[k])
print(f"cases x methods in the re-run: {len(after)}; in earlier records: {len(before)}")
print(f"identical: {len(set(after) & set(before)) - len(changed)}; changed: {len(changed)}")
print(f"only in the re-run: {len(missing)}; only in earlier records: {len(gone)}")
for k in changed:
    print("CHANGED", k, source[k], before[k], "->", after[k])
for k in missing:
    print("NEW", k, after[k])
for k in gone:
    print("MISSING", k, source[k])
