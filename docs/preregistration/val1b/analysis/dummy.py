"""Dummy study data for testing analyse.py before any real data exists.

Everything here is invented by this script (data_class = dummy). It exercises the file
formats and every decision rule; it says nothing about CodeAdapt or about any person.

    python3 dummy.py OUT_DIR [--scenario pass|few_named|disagree|false_alarm]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATEGORIES = json.loads((HERE.parent / "forms" / "categories.json").read_text())
PROBLEMS = ("lower-bound", "count-occurrences", "last-less-than", "first-true")
SCENARIOS = ("pass", "few_named", "disagree", "false_alarm")


def write(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def generate(out: Path, scenario: str, seed: int = 1) -> None:
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    programs, s1, s2, fixes, ca = [], {"L1": [], "L2": []}, {"L1": [], "L2": []}, [], []
    adjudication = []
    n_named = {"pass": 40, "few_named": 6, "disagree": 30, "false_alarm": 30}[scenario]
    pid = 0
    for author in range(5):
        for prob in PROBLEMS:
            cats = list(CATEGORIES[prob]["categories"])
            for j in range(6):  # 5 incorrect + 1 correct per author and problem
                pid += 1
                p = f"P{pid:03d}"
                correct = j == 5
                programs.append(
                    {
                        "program": p,
                        "problem": prob,
                        "author": f"A{author + 1}",
                        "declared": "correct" if correct else "incorrect",
                    }
                )
                true_cat = rng.choice(cats)
                line = rng.randint(3, 15)
                for lab in ("L1", "L2"):
                    cat = true_cat
                    if scenario == "disagree" and rng.random() < 0.6:
                        cat = rng.choice([*cats, "other-single", "unclear"])
                    s1[lab].append(
                        {
                            "program": p,
                            "correctness": "correct" if correct else "incorrect",
                            "fault_lines": ""
                            if correct
                            else str(
                                line if scenario != "disagree" or rng.random() < 0.5 else line + 3
                            ),
                            "what_is_wrong": "" if correct else "dummy description",
                            "should_be": "",
                            "minimal_fix": "" if correct else "dummy fix",
                            "other_errors": "",
                            "confidence": rng.randint(1, 3),
                            "notes": "",
                        }
                    )
                    s2[lab].append(
                        {
                            "program": p,
                            "category": "" if correct else cat,
                            "other_description": "",
                            "skill": ""
                            if correct
                            else CATEGORIES[prob]["category_skills"].get(cat, "none"),
                            "mapping_confidence": rng.randint(1, 3),
                            "change_note": "",
                        }
                    )
                    fixes.append(
                        {"program": p, "labeller": lab, "validity": "none" if correct else "valid"}
                    )
                if not correct and s2["L1"][-1]["category"] != s2["L2"][-1]["category"]:
                    adjudication.append(
                        {
                            "program": p,
                            "trigger": "category_differs",
                            "adjudicated_category": true_cat,
                            "adjudicated_skill": "",
                            "reason": "dummy",
                            "author_note_consulted": "no",
                        }
                    )
                for version in ("1.2", "1.1"):
                    outcome, model = "unmodelled_behaviour", ""
                    if correct:
                        outcome = (
                            "hypothesis_supported"
                            if scenario == "false_alarm" and pid == 6
                            else "no_failure_observed"
                        )
                        model = (
                            CATEGORIES[prob]["categories"][cats[0]]
                            if outcome != "no_failure_observed"
                            else ""
                        )
                    elif pid % 120 < n_named * 120 // 100 or (
                        scenario != "few_named" and rng.random() < n_named / 100
                    ):
                        outcome, model = (
                            "hypothesis_supported",
                            CATEGORIES[prob]["categories"][true_cat],
                        )
                    ca.append(
                        {
                            "program": p,
                            "method_version": version,
                            "outcome": outcome,
                            "selected_model": model,
                            "qualified": "false",
                            "reproducible": "true",
                        }
                    )
    write(out / "programs.csv", programs)
    for lab in ("L1", "L2"):
        write(out / f"stage1_{lab}.csv", s1[lab])
        write(out / f"stage2_{lab}.csv", s2[lab])
    write(out / "fix_validity.csv", fixes)
    write(out / "codeadapt.csv", ca)
    if adjudication:
        write(out / "adjudication.csv", adjudication)
    (out / "DUMMY_DATA.txt").write_text(
        f"Invented test data, scenario {scenario}. Not study data.\n"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--scenario", choices=SCENARIOS, default="pass")
    a = ap.parse_args()
    generate(a.out, a.scenario)
