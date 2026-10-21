"""Write comparison.md from val1a.json and heldout-calibration.json (ADR-027 §8 item 3).

Run from the repository root: python3 docs/evaluation/adr027-2026-10-21/summarise.py
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
NAMED = "hypothesis_supported"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def frac(k: int, n: int) -> str:
    if n == 0:
        return "0/0"
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({100 * k / n:.0f}%, CI {100 * lo:.0f}-{100 * hi:.0f}%)"


def is_buggy(row: dict[str, Any]) -> bool:
    if row["set"] == "val1a":
        return row["category"] == "incorrect_failing"
    return row["truth"] != "correct"


def truth(row: dict[str, Any], lenient: bool = False) -> str:
    if row["set"] == "val1a":
        return row["truth_lenient" if lenient else "truth_strict"]
    return row["truth"]


def aggregate(rows: list[dict[str, Any]], v: str) -> dict[str, str]:
    buggy = [r for r in rows if is_buggy(r)]
    correct = [r for r in rows if not is_buggy(r) and truth(r) == "correct"]
    named = [r for r in buggy if r[v]["outcome"] == NAMED]
    wrong = [r for r in named if r[v]["selected_model"] != truth(r)]
    out = {
        "Buggy cases": str(len(buggy)),
        "Named diagnoses (coverage)": frac(len(named), len(buggy)),
        "Wrong name": frac(len(wrong), len(named)),
        "Unqualified named": str(
            sum(
                r[v]["evidence_strength"] == "multiple" and not r[v]["known_limitation"]
                for r in named
            )
        ),
        "non_termination_observed": str(
            sum(r[v]["outcome"] == "non_termination_observed" for r in buggy)
        ),
        "Abstentions by outcome": ", ".join(
            f"{k}: {n}"
            for k, n in sorted(Counter(r[v]["outcome"] for r in buggy if r[v]["outcome"] != NAMED).items())
        )
        or "none",
        "`incorrect` skill observations": ", ".join(
            f"{k}: {n}"
            for k, n in sorted(
                Counter(
                    o.split(":")[0]
                    for r in rows
                    for o in r[v]["skill_observations"]
                    if o.endswith(":incorrect")
                ).items()
            )
        )
        or "none",
        "Hints shown on buggy cases": str(sum(r[v]["feedback"]["hint_shown"] for r in buggy)),
        "Recommendations targeting a diagnosed skill": str(
            sum(
                r[v]["recommendation"]["rule"] in ("hypothesis_supported", "ambiguous")
                for r in rows
            )
        ),
        "Correct code with no failure observed": frac(
            sum(r[v]["outcome"] == "no_failure_observed" for r in correct), len(correct)
        ),
    }
    if rows and rows[0]["set"] == "val1a":
        wrong_l = [r for r in named if r[v]["selected_model"] != truth(r, lenient=True)]
        out["Wrong name (lenient labels)"] = frac(len(wrong_l), len(named))
    return out


def same(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Equal apart from the policy version label (1.3 vs 1.4)."""

    def strip(x: dict[str, Any]) -> dict[str, Any]:
        rec = {k: v for k, v in x["recommendation"].items() if k != "policy_version"}
        return {**x, "recommendation": rec}

    return strip(a) == strip(b)


def case_table(rows: list[dict[str, Any]], changed_only: bool) -> list[str]:
    head = [
        "| Case | Truth | v1.1 outcome (model) | v1.2 outcome (model) | v1.1 → v1.2 skill obs | "
        "v1.1 → v1.2 recommendation | hint |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    out = []
    for r in rows:
        a, b = r["v1.1"], r["v1.2"]
        if changed_only and same(a, b):
            continue

        def oc(x: dict[str, Any]) -> str:
            q = ""
            if x["outcome"] == NAMED:
                q = " q" if x["evidence_strength"] == "single_behaviour" or x["known_limitation"] else ""
                return f"named ({x['selected_model']}{q})"
            return x["outcome"]

        def obs(x: dict[str, Any]) -> str:
            bad = [o.split(":")[0] for o in x["skill_observations"] if o.endswith(":incorrect")]
            return f"{len(x['skill_observations'])} obs" + (f", incorrect {','.join(bad)}" if bad else "")

        def rec(x: dict[str, Any]) -> str:
            rr = x["recommendation"]
            t = ",".join(rr["target_skills"]) or "no skill"
            return f"{rr['rule']} {rr['action']} {rr['problem']} ({t})"

        out.append(
            f"| {r['case']} | {truth(r)} | {oc(a)} | {oc(b)} | {obs(a)} → {obs(b)} | "
            f"{rec(a)} → {rec(b)} | {'yes' if a['feedback']['hint_shown'] else 'no'} → "
            f"{'yes' if b['feedback']['hint_shown'] else 'no'} |"
        )
    return head + out if out else ["No case changed."]


def main() -> None:
    sets: dict[str, list[dict[str, Any]]] = {}
    val1a = json.loads((HERE / "val1a.json").read_text())
    sets["VAL1-A (lower-bound mutants, replayed)"] = val1a
    hc = HERE / "heldout-calibration.json"
    if hc.exists():
        rows = json.loads(hc.read_text())
        sets["Held-out"] = [r for r in rows if r["set"] == "heldout"]
        sets["Calibration"] = [r for r in rows if r["set"] == "calibration"]
    lines = [
        "# ADR-027 comparison: method v1.1 vs v1.2, case by case",
        "",
        "Generated by `summarise.py`. Synthetic data only: none of this is real-student accuracy.",
        "q = qualified (single behaviour or documented collision).",
        "",
    ]
    for name, rows in sets.items():
        a, b = aggregate(rows, "v1.1"), aggregate(rows, "v1.2")
        lines += [f"## {name}", "", "| Metric | v1.1 | v1.2 |", "| --- | --- | --- |"]
        lines += [f"| {k} | {a[k]} | {b[k]} |" for k in a]
        changed = sum(not same(r["v1.1"], r["v1.2"]) for r in rows)
        lines += ["", f"Cases whose outcome or consequences changed: {changed} of {len(rows)}.", ""]
        lines += case_table(rows, changed_only=True) + [""]
    (HERE / "comparison.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
