"""Skills that no error model can give negative evidence for, from the measured fingerprints.

Usage (from the repository root, after `codeadapt-content report`):
    python3 docs/evaluation/l20-original-s1-2026-10-26/effective_positive_only.py

The content check (ProblemSpec, `positive_only_skills`) counts a model as evidence-capable
when it carries no `known_limitation`. Diagnosis v1.3 can name a model unqualified only if,
on its own fingerprint, it also passes these rules, so a model that fails any of them never
gives an `incorrect` observation:
  - rule 4b: no detecting test times out (a time limit is a symptom, never named);
  - rule 7: at least 2 detecting tests (min_support);
  - single behaviour group: named but qualified (no failure evidence);
  - rule 8a: its prediction is not the same on every test.
Read from docs/content-reports/*.md and content/demo/*/problem.toml. Measured on the committed
tests only; a program that matches a model only partly is not covered.
"""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def cells(line: str) -> list[str]:
    return [c.strip().strip("`") for c in line.strip().strip("|").split("|")]


def report(slug: str) -> tuple[dict[str, list[str]], list[str], dict[str, tuple[int, int]]]:
    lines = (ROOT / "docs/content-reports" / f"{slug}.md").read_text().splitlines()
    m = lines.index("## Matrix")
    head = next(i for i in range(m, len(lines)) if lines[i].startswith("| Test"))
    names = cells(lines[head])[2:]
    columns: dict[str, list[str]] = {n: [] for n in names}
    reference: list[str] = []
    for line in lines[head + 2 :]:
        if not line.startswith("|"):
            break
        row = cells(line)
        reference.append(row[1])
        for n, c in zip(names, row[2:], strict=True):
            columns[n].append(row[1] if c == "·" else c)
    e = lines.index("## Error models")
    stats = {}
    for line in lines[e + 4 :]:
        if not line.startswith("|"):
            break
        row = cells(line)
        stats[row[0]] = (int(row[2]), int(row[3]))
    return columns, reference, stats


def why_not_nameable(col: list[str], ref: list[str], tests: int, groups: int) -> list[str]:
    reasons = []
    if any(c == "time_limit" for c, r in zip(col, ref, strict=True) if c != r):
        reasons.append("4b time limit")
    if tests < 2:
        reasons.append("7 support < 2")
    if groups < 2:
        reasons.append("single behaviour")
    if len(set(col)) == 1:
        reasons.append("8a constant")
    return reasons


def main() -> None:
    print("problem | skill | declared positive-only | models and why none gives negative evidence")
    for toml in sorted((ROOT / "content/demo").glob("*/problem.toml")):
        spec = tomllib.loads(toml.read_text())
        slug = spec["slug"]
        columns, ref, stats = report(slug)
        declared = set(spec.get("positive_only_skills", {}))
        by_skill: dict[str, list[tuple[str, list[str]]]] = {s: [] for s in spec["skills"]}
        for model in spec["error_models"]:
            reasons = why_not_nameable(columns[model["key"]], ref, *stats[model["key"]])
            if model.get("known_limitation"):
                reasons.append("known_limitation")
            by_skill[model["skill"]].append((model["key"], reasons))
        for skill, models in sorted(by_skill.items()):
            if all(r for _, r in models):
                detail = "; ".join(f"{k}: {', '.join(r)}" for k, r in models) or "no model"
                flag = "yes" if skill in declared else "NO (effective only)"
                print(f"{slug} | {skill} | {flag} | {detail}")


if __name__ == "__main__":
    main()
