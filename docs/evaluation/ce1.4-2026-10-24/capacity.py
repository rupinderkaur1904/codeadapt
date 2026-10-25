"""CE1.4 family report: observation capacity and BKT sensitivity on the current bank.

Technical measurements only. Run from backend/:
    uv run python ../docs/evaluation/ce1.4-2026-10-24/capacity.py

Capacity per skill, under LM1 (one counted observation per problem version, L1):
- `problems`: problems whose skill map gives the skill at least one test, so an attempt can
  yield one observation on it (an upper bound per learner, one version per problem);
- `incorrect-capable`: problems with at least one model on the skill that v1.3 can name
  without qualification, i.e. not a documented collision and not time-limit-only in the
  measured content report (ADR-027: a time limit is never named).
Then the spread of P(known) over the 81-point grid of the 2026-10-17 sensitivity check, for
all-correct and one-incorrect-then-correct sequences up to each skill's capacity. Nothing here
estimates any real learner or validates any parameter.
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path

from codeadapt.adaptation import SkillMap
from codeadapt.content import load_catalogue
from codeadapt.learner import ASSUMED_PARAMS_1, BktParams, update

ROOT = Path(__file__).resolve().parents[3]
GRID = {
    "p_init": (0.1, 0.3, 0.5),
    "p_learn": (0.05, 0.1, 0.2),
    "p_guess": (0.1, 0.2, 0.3),
    "p_slip": (0.05, 0.1, 0.2),
}


def time_limit_only(slug: str) -> set[str]:
    """Models whose every detecting cell in the measured report is `time_limit`."""
    lines = (ROOT / "docs" / "content-reports" / f"{slug}.md").read_text().splitlines()
    start = lines.index("## Matrix")
    header = next(line for line in lines[start:] if line.startswith("| Test |"))
    models = [c.strip(" `") for c in header.strip("|").split("|")][2:]
    cells: dict[str, list[str]] = {m: [] for m in models}
    for line in lines[lines.index(header) + 2 :]:
        if not line.startswith("| `"):
            break
        row = [c.strip() for c in line.strip("|").split("|")][2:]
        for m, c in zip(models, row, strict=True):
            if c != "·":
                cells[m].append(c)
    return {m for m, cs in cells.items() if cs and all(c == "time_limit" for c in cs)}


def trace(seq: str, params: BktParams) -> float:
    p = params.p_init
    for obs in seq:
        p = update(p, obs == "C", params)
    return p


def main() -> None:
    problems = load_catalogue(ROOT / "content" / "demo")
    skills: dict[str, dict[str, list[str]]] = {}
    for p in problems:
        smap = SkillMap.from_spec(p.spec, p.version)
        tl = time_limit_only(p.spec.slug)
        tested = {s for ss in smap.test_skills.values() for s in ss}
        for s in tested:
            skills.setdefault(s, {"problems": [], "incorrect": []})["problems"].append(p.spec.slug)
        for m in p.spec.error_models:
            if m.key in smap.documented_collisions or m.key in tl:
                continue
            entry = skills.setdefault(m.skill, {"problems": [], "incorrect": []})
            if p.spec.slug not in entry["incorrect"]:
                entry["incorrect"].append(p.spec.slug)
    print(f"bank: {len(problems)} problems; "
          f"{sum(p.spec.recommendable for p in problems)} recommendable by policy v1")
    print()
    print("| Skill | Max counted observations (problems) | Problems that can give `incorrect` |")
    print("| --- | --- | --- |")
    for s in sorted(skills):
        e = skills[s]
        print(f"| {s} | {len(e['problems'])} | {len(e['incorrect'])} |")
    grid = [
        BktParams(name="grid", **dict(zip(GRID, v, strict=True)))
        for v in itertools.product(*GRID.values())
    ]
    cap = max(len(e["problems"]) for e in skills.values())
    print()
    print(f"P(known) spread over {len(grid)} parameter sets (assumed set in brackets):")
    print()
    print("| Sequence | min | max | assumed |")
    print("| --- | --- | --- | --- |")
    for n in sorted({1, 2, 3, 5, 8, cap}):
        for seq in ("C" * n, "I" + "C" * (n - 1)):
            values = [trace(seq, g) for g in grid]
            print(f"| {seq} | {min(values):.3f} | {max(values):.3f} | "
                  f"{trace(seq, ASSUMED_PARAMS_1):.3f} |")


if __name__ == "__main__":
    main()
