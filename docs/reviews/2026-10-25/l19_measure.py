"""L19 measurement: skill observations that incorrect programs produce under method v1.3.

Reads the committed ADR-030 replay (docs/evaluation/adr030-replay-2026-10-22/cases.json),
whose `candidate` runs equal production method v1.3 (docs/evaluation/adr030-2026-10-23) and
carry the skill observations computed by the production pipeline (current evidence rules,
including rule C). Only VAL1-A and VAL1-A2 synthetic mutants labelled `incorrect_failing`
are used. Synthetic single-edit mutants: the counts describe this corpus, not real code.

Run from the repository root: python3 docs/reviews/2026-10-25/l19_measure.py
"""

import collections
import json

cases = json.load(open("docs/evaluation/adr030-replay-2026-10-22/cases.json"))
rows = collections.defaultdict(collections.Counter)
for case in cases:
    if case["set"] not in ("val1a", "val1a2") or case["category"] != "incorrect_failing":
        continue
    run = case["runs"]["candidate"][0]
    named = (
        run["outcome"] == "hypothesis_supported"
        and run["evidence_strength"] != "single_behaviour"
        and not run["known_limitation"]
    )
    correct = [o.split(":")[0] for o in run["skill_observations"] if o.endswith(":correct")]
    incorrect = [o for o in run["skill_observations"] if o.endswith(":incorrect")]
    for key in (case["problem"], "ALL"):
        row = rows[key]
        row["incorrect programs"] += 1
        row["named (unqualified)"] += named
        row["not named"] += not named
        row["not named, >=1 correct obs"] += (not named) and bool(correct)
        row["correct obs from not named"] += 0 if named else len(correct)
        row["correct obs from named"] += len(correct) if named else 0
        row["incorrect obs"] += len(incorrect)
        for skill in correct if not named else ():
            row[f"  not named -> {skill}"] += 1

for key, row in rows.items():
    print(key)
    for name, value in row.items():
        print(f"  {name}: {value}")
