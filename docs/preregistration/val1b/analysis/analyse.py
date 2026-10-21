"""VAL1-B pre-registered analysis (protocol §6 and §8). Standard library only.

Usage:
    python3 analyse.py DATA_DIR [--out OUT_DIR]

DATA_DIR holds the committed study files (formats in ../forms/README.md):
    programs.csv            program, problem, author, declared        (declared: correct|incorrect)
    stage1_L1.csv, stage1_L2.csv
    stage2_L1.csv, stage2_L2.csv
    adjudication.csv
    fix_validity.csv        program, labeller, validity  (valid|invalid|does-not-compile|none)
    codeadapt.csv           program, method_version, outcome, selected_model, qualified,
                            reproducible  (one row per program and method version)
and ../forms/categories.json maps each problem's category ids to model keys and skills.

Writes results.json and report.md. Every decision rule here is fixed by the protocol; do
not change it after any study data exists. A precision endpoint that cannot be evaluated is
never counted as a pass.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CATEGORIES = HERE.parent / "forms" / "categories.json"
BOOTSTRAP = 2000
SEED = 20261021
MIN_PRECISION_N = 12
NAMED = "hypothesis_supported"
SYMPTOM = "non_termination_observed"


# ----------------------------------------------------------------------------- statistics
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    n = len(pairs)
    if n == 0:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if pe == 1:
        return 1.0 if po == 1 else 0.0
    return (po - pe) / (1 - pe)


def kappa_ci(pairs: list[tuple[str, str]]) -> tuple[float, float] | None:
    """Percentile bootstrap, fixed seed, so the interval is reproducible."""
    if not pairs:
        return None
    rng = random.Random(SEED)
    values = []
    for _ in range(BOOTSTRAP):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        k = kappa(sample)
        if k is not None:
            values.append(k)
    values.sort()
    return (values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1])


def ratio(k: int, n: int) -> dict[str, Any]:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "p": (k / n if n else None), "ci": [round(lo, 4), round(hi, 4)]}


# ----------------------------------------------------------------------------- decisions
def classify(below: bool, adequate: bool) -> str:
    return "below" if below else "adequate" if adequate else "inconclusive"


def decide_proportion(
    r: dict[str, Any], below_upper: float, ok_point: float, ok_lower: float
) -> str:
    if r["n"] == 0:
        return "not_evaluable"
    lo, hi = r["ci"]
    return classify(hi < below_upper, r["p"] >= ok_point and lo >= ok_lower)


def decide_kappa(k: float | None, ci: tuple[float, float] | None) -> str:
    if k is None or ci is None:
        return "not_evaluable"
    return classify(ci[1] < 0.6, k >= 0.6 and ci[0] >= 0.4)


def overall(decisions: dict[str, str]) -> str:
    """Protocol §8. `pass` needs every primary result adequate, S3 included."""
    if decisions["S5"] == "below":
        return "blocking_defect"
    failed = [k for k in ("S0", "S1", "S2", "S3", "S4") if decisions[k] == "below"]
    if failed:
        return "below:" + ",".join(failed)
    if any(decisions[k] in ("inconclusive",) for k in ("S0", "S1", "S2", "S3", "S4")):
        return "inconclusive"
    if decisions["S3"] == "not_evaluable":
        return "not_established:precision_not_evaluable"
    if any(decisions[k] == "not_evaluable" for k in ("S0", "S1", "S2", "S4")):
        return "not_established"
    return "pass"


# ----------------------------------------------------------------------------- loading
def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def by_program(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for r in rows:
        if r["program"] in out:
            raise ValueError(f"duplicate program {r['program']}")
        out[r["program"]] = r
    return out


def lines(text: str) -> set[int]:
    return {int(x) for x in text.replace(";", ",").replace(" ", ",").split(",") if x.strip()}


def analyse(data: Path, categories: dict[str, Any], primary_version: str) -> dict[str, Any]:
    programs = by_program(read(data / "programs.csv"))
    s1 = {lab: by_program(read(data / f"stage1_{lab}.csv")) for lab in ("L1", "L2")}
    s2 = {lab: by_program(read(data / f"stage2_{lab}.csv")) for lab in ("L1", "L2")}
    adj = (
        by_program(read(data / "adjudication.csv")) if (data / "adjudication.csv").exists() else {}
    )
    fixes = {(r["program"], r["labeller"]): r["validity"] for r in read(data / "fix_validity.csv")}
    ca_rows = [r for r in read(data / "codeadapt.csv")]
    versions = sorted({r["method_version"] for r in ca_rows})
    codeadapt = {v: by_program([r for r in ca_rows if r["method_version"] == v]) for v in versions}
    for lab in ("L1", "L2"):
        missing = set(programs) - set(s1[lab]) | set(programs) - set(s2[lab])
        if missing:
            raise ValueError(f"{lab} has no label for {sorted(missing)}")

    both_incorrect = [
        p for p in programs if all(s1[lab][p]["correctness"] == "incorrect" for lab in ("L1", "L2"))
    ]
    both_correct = [
        p
        for p in programs
        if programs[p]["declared"] == "correct"
        and all(s1[lab][p]["correctness"] == "correct" for lab in ("L1", "L2"))
    ]

    # P1: same faulty statement and both minimal fixes valid.
    same_statement = [
        p
        for p in both_incorrect
        if lines(s1["L1"][p]["fault_lines"]) & lines(s1["L2"][p]["fault_lines"])
    ]
    p1_agree = [
        p
        for p in same_statement
        if fixes.get((p, "L1")) == "valid" and fixes.get((p, "L2")) == "valid"
    ]
    p1 = ratio(len(p1_agree), len(both_incorrect))
    p1_statement = ratio(len(same_statement), len(both_incorrect))

    # P2, P3: Cohen's kappa on stage-2 category and skill, programs both called incorrect.
    cat_pairs = [(s2["L1"][p]["category"], s2["L2"][p]["category"]) for p in both_incorrect]
    skill_pairs = [(s2["L1"][p]["skill"], s2["L2"][p]["skill"]) for p in both_incorrect]
    k2, k2ci = kappa(cat_pairs), kappa_ci(cat_pairs)
    k3, k3ci = kappa(skill_pairs), kappa_ci(skill_pairs)

    results: dict[str, Any] = {"primary_method_version": primary_version, "versions": {}}
    for version, ca in codeadapt.items():
        missing = set(programs) - set(ca)
        if missing:
            raise ValueError(f"no CodeAdapt result for {sorted(missing)} under {version}")
        named = [p for p in both_incorrect if ca[p]["outcome"] == NAMED]
        p4 = ratio(len(named), len(both_incorrect))

        # P5: unqualified named diagnoses on programs whose stage-2 categories agree.
        def matches(p: str, category: str) -> bool:
            key = categories[programs[p]["problem"]]["categories"].get(category)
            return key is not None and key == ca[p]["selected_model"]

        agreed = [
            p
            for p in named
            if ca[p]["qualified"] == "false"
            and s2["L1"][p]["category"] == s2["L2"][p]["category"]
            and s2["L1"][p]["category"] != "unclear"
        ]
        p5 = ratio(sum(matches(p, s2["L1"][p]["category"]) for p in agreed), len(agreed))
        p5_evaluable = len(agreed) >= MIN_PRECISION_N

        flagged = [p for p in both_correct if ca[p]["outcome"] in (NAMED, SYMPTOM)]
        p6 = {
            "false_alarms": len(flagged),
            "correct_programs": len(both_correct),
            "programs": flagged,
        }

        decisions = {
            "S0": decide_proportion(p1, 0.60, 0.75, 0.60),
            "S1": decide_kappa(k2, k2ci),
            "S2": decide_kappa(k3, k3ci),
            "S3": (
                classify(p5["ci"][1] < 0.90, p5["ci"][0] >= 0.70)
                if p5_evaluable
                else "not_evaluable"
            ),
            "S4": decide_proportion(p4, 0.20, 0.0, 0.20),
            "S5": "below" if flagged else ("adequate" if both_correct else "not_evaluable"),
        }

        # Exploratory (no decision rests on these).
        adjudicated = {
            p: (adj[p]["adjudicated_category"] if p in adj else s2["L1"][p]["category"])
            for p in named
            if p in adj or s2["L1"][p]["category"] == s2["L2"][p]["category"]
        }
        unq = [p for p in adjudicated if ca[p]["qualified"] == "false"]
        qualified = [p for p in named if ca[p]["qualified"] == "true"]
        exploratory = {
            "precision_vs_adjudicated_unqualified": ratio(
                sum(matches(p, adjudicated[p]) for p in unq), len(unq)
            ),
            "qualified_diagnoses": len(qualified),
            "precision_vs_agreed_qualified": ratio(
                sum(
                    matches(p, s2["L1"][p]["category"])
                    for p in qualified
                    if s2["L1"][p]["category"] == s2["L2"][p]["category"]
                ),
                sum(s2["L1"][p]["category"] == s2["L2"][p]["category"] for p in qualified),
            ),
            "outcomes_on_both_incorrect": dict(Counter(ca[p]["outcome"] for p in both_incorrect)),
            "non_termination_observed": len(
                [p for p in both_incorrect if ca[p]["outcome"] == SYMPTOM]
            ),
            "coverage_by_problem": {
                prob: ratio(
                    sum(1 for p in named if programs[p]["problem"] == prob),
                    sum(1 for p in both_incorrect if programs[p]["problem"] == prob),
                )
                for prob in sorted({programs[p]["problem"] for p in programs})
            },
            "p1_minus_category_raw_agreement": (
                None
                if not cat_pairs or p1["p"] is None
                else round(p1["p"] - sum(a == b for a, b in cat_pairs) / len(cat_pairs), 4)
            ),
            "reproducible": ratio(
                sum(ca[p]["reproducible"] == "true" for p in programs), len(programs)
            ),
        }
        results["versions"][version] = {
            "P4_coverage": p4,
            "P5_agreed_precision": {**p5, "evaluable": p5_evaluable, "min_n": MIN_PRECISION_N},
            "P6_false_alarms": p6,
            "decisions": decisions,
            "overall": overall(decisions),
            "exploratory": exploratory,
        }

    results["labellers"] = {
        "programs": len(programs),
        "both_incorrect": len(both_incorrect),
        "both_correct_and_declared_correct": len(both_correct),
        "correctness_agreement": ratio(
            sum(s1["L1"][p]["correctness"] == s1["L2"][p]["correctness"] for p in programs),
            len(programs),
        ),
        "P1_open_ended_agreement": p1,
        "P1_statement_only": p1_statement,
        "P2_category_kappa": {"kappa": k2, "ci": k2ci, "n": len(cat_pairs)},
        "P3_skill_kappa": {"kappa": k3, "ci": k3ci, "n": len(skill_pairs)},
        "confidence_vs_category_agreement": {
            str(c): ratio(
                sum(
                    1
                    for p in both_incorrect
                    if min(int(s2[lab][p]["mapping_confidence"]) for lab in ("L1", "L2")) == c
                    and s2["L1"][p]["category"] == s2["L2"][p]["category"]
                ),
                sum(
                    1
                    for p in both_incorrect
                    if min(int(s2[lab][p]["mapping_confidence"]) for lab in ("L1", "L2")) == c
                ),
            )
            for c in (1, 2, 3)
        },
        "stage2_change_notes": sum(
            bool(s2[lab][p].get("change_note")) for lab in ("L1", "L2") for p in programs
        ),
    }
    return results


def render(results: dict[str, Any]) -> str:
    lab = results["labellers"]

    def fmt(r: dict[str, Any]) -> str:
        if not r["n"]:
            return "0/0"
        return f"{r['k']}/{r['n']} ({100 * r['p']:.0f}%, 95% CI {100 * r['ci'][0]:.0f}–{100 * r['ci'][1]:.0f}%)"

    def fk(d: dict[str, Any]) -> str:
        if d["kappa"] is None:
            return "not evaluable"
        return f"κ = {d['kappa']:.2f} (95% CI {d['ci'][0]:.2f}–{d['ci'][1]:.2f}, n = {d['n']})"

    out = [
        "# VAL1-B results (pre-registered analysis)",
        "",
        "Synthetic-independent programs written by volunteers. Not real-student accuracy, "
        "not learning, not mastery.",
        "",
        "## Labellers",
        "",
        f"- P1 open-ended agreement: {fmt(lab['P1_open_ended_agreement'])}",
        f"- P1 statement only: {fmt(lab['P1_statement_only'])}",
        f"- P2 category: {fk(lab['P2_category_kappa'])}",
        f"- P3 skill: {fk(lab['P3_skill_kappa'])}",
        f"- Correctness agreement: {fmt(lab['correctness_agreement'])}",
        "",
    ]
    for version, v in results["versions"].items():
        tag = " (primary)" if version == results["primary_method_version"] else " (secondary)"
        p5 = v["P5_agreed_precision"]
        out += [
            f"## Method v{version}{tag}",
            "",
            f"- P4 named coverage: {fmt(v['P4_coverage'])}",
            f"- P5 agreed-label precision: {fmt(p5)}"
            + (
                ""
                if p5["evaluable"]
                else f" — not evaluable (fewer than {p5['min_n']}); not a pass"
            ),
            f"- P6 false alarms on correct code: {v['P6_false_alarms']['false_alarms']}"
            f"/{v['P6_false_alarms']['correct_programs']}",
            "",
            "| Rule | Result |",
            "| --- | --- |",
            *[f"| {k} | {d} |" for k, d in v["decisions"].items()],
            "",
            f"**Overall: {v['overall']}**",
            "",
        ]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--primary", required=True, help="pre-registered primary method version")
    args = parser.parse_args()
    results = analyse(args.data, json.loads(CATEGORIES.read_text()), args.primary)
    out = args.out or args.data
    (out / "results.json").write_text(json.dumps(results, indent=1) + "\n")
    (out / "report.md").write_text(render(results) + "\n")
    print(render(results))


if __name__ == "__main__":
    main()
