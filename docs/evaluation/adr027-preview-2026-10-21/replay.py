"""Preview of the proposed ADR-027 rule on the stored VAL1-A results (no re-execution).

This is a replay of the decision rule on recorded observations, not the approved re-run
that ADR-027 §8 requires. It changes no production code: it reads the v1.1 records in
docs/evaluation/val1a-2026-10-21/results/ and applies the proposed rule 4b by hand.

Proposed rule 4b: after rules 1-4 (compile, execution, unreliable, no failure), if any
reliable failing test ended at the CPU-time limit, the outcome is
`non_termination_observed`; no model is selected and the candidates are kept only as
research information.

Run from the repository root: python3 docs/evaluation/adr027-preview-2026-10-21/replay.py
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VAL1A = ROOT / "docs/evaluation/val1a-2026-10-21/results"
OUT = Path(__file__).resolve().parent
PASS_THROUGH = {"compile_error", "execution_error", "unreliable_evidence", "no_failure_observed"}
TERMINATION_MODELS = {"no_progress_update", "closed_loop_hi_mid"}  # lower-bound models


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def replay_run(run: dict) -> str:
    if run["outcome"] in PASS_THROUGH:
        return run["outcome"]
    excluded = set(run["excluded"])
    timed_out = [
        k for k in run["failing_tests"]
        if k not in excluded and run["signatures"][k] == "time_limit"
    ]
    return "non_termination_observed" if timed_out else run["outcome"]


def main() -> None:
    cases = {c["id"]: c for c in json.loads((VAL1A / "cases.json").read_text())}
    runs = {}
    for line in (VAL1A / "pipeline.jsonl").read_text().splitlines():
        rec = json.loads(line)
        runs[rec["program"]] = rec["runs"]

    rows = []
    for cid, case in sorted(cases.items()):
        outs = {replay_run(r) for r in runs[cid]}
        assert len(outs) == 1, (cid, outs)  # both recorded runs give the same replayed outcome
        new = outs.pop()
        named = case["model"] if new == "hypothesis_supported" else None
        rows.append({
            "id": cid,
            "style": case["style"],
            "category": case["category"],
            "label_strict": case["label_strict"],
            "label_lenient": case["label_lenient"],
            "v1_1_outcome": case["outcome"],
            "v1_1_model": case["model"],
            "v1_1_qualified": case["qualified"],
            "v1_2_outcome": new,
            "v1_2_model": named,
            "changed": new != case["outcome"],
        })

    inc = [r for r in rows if r["category"] == "incorrect_failing"]
    summary: dict[str, object] = {"programs": len(rows), "incorrect_failing": len(inc)}
    for ver in ("v1_1", "v1_2"):
        named = [r for r in inc if r[f"{ver}_outcome"] == "hypothesis_supported"]
        wrong_s = [r for r in named if r[f"{ver}_model"] != r["label_strict"]]
        wrong_l = [r for r in named if r[f"{ver}_model"] != r["label_lenient"]]
        term = [r for r in named if r[f"{ver}_model"] in TERMINATION_MODELS]
        summary[ver] = {
            "outcomes": dict(Counter(r[f"{ver}_outcome"] for r in inc)),
            "named": len(named),
            "named_coverage": [len(named), len(inc), [round(x, 3) for x in wilson(len(named), len(inc))]],
            "wrong_strict": [len(wrong_s), len(named), [round(x, 3) for x in wilson(len(wrong_s), len(named))]],
            "wrong_lenient": [len(wrong_l), len(named), [round(x, 3) for x in wilson(len(wrong_l), len(named))]],
            "named_termination_models": len(term),
            "correct_named_strict": len(named) - len(wrong_s),
            # Unqualified named diagnoses are the only source of `incorrect` skill
            # observations (ledger policy 1.2); termination models map to loop_termination.
            "incorrect_loop_termination_observations": sum(
                1 for r in term if not r[f"{ver}_qualified" if ver == "v1_1" else "v1_1_qualified"]
            ),
        }
    nt = [r for r in inc if r["v1_2_outcome"] == "non_termination_observed"]
    summary["non_termination_observed"] = {
        "programs": len(nt),
        "from_v1_1": dict(Counter(f'{r["v1_1_outcome"]}:{r["v1_1_model"]}' for r in nt)),
        "strict_label_is_termination_model": sum(r["label_strict"] in TERMINATION_MODELS for r in nt),
        "by_style": dict(Counter(r["style"] for r in nt)),
    }
    summary["changed_programs"] = sum(r["changed"] for r in rows)
    summary["changed_outside_incorrect_failing"] = sum(
        r["changed"] for r in rows if r["category"] != "incorrect_failing"
    )
    (OUT / "val1a-replay.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
