"""Generate the 25-problem status matrix (bank-status-matrix.md) from the committed content.

Usage (from the repository root): python3 docs/reviews/2026-10-26/bank-status/bank_matrix.py

The mechanical columns are read from content/demo/*/problem.toml, docs/content-reports/*.md
and eval/heldout/. The review columns (alternative-cause search, research review status,
skill-mapping notes) restate committed records and decisions and are written in REVIEW below.
Nothing here changes any problem, and no column means "research-validated".
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(
    0, str(Path(__file__).resolve().parents[3] / "evaluation/l20-original-s1-2026-10-26")
)
from effective_positive_only import report, why_not_nameable  # noqa: E402

ORIGINAL = {"lower-bound", "count-occurrences", "last-less-than", "first-true"}
UNREVIEWED = {
    "integer-sqrt",
    "min-capacity",
    "upper-bound",
    "exact-search",
    "last-occurrence",
    "rotated-min",
    "rotated-search",
    "peak-index",
}
SEARCH_2510 = {
    "upper-bound",
    "exact-search",
    "last-occurrence",
    "rotated-search",
    "peak-index",
    "integer-sqrt",
}

# Alternative-cause review per problem, from the committed records.
ALT = {
    **dict.fromkeys(ORIGINAL, "exhaustive + random search 2026-10-26 (l20-search-original.md)"),
    **dict.fromkeys(SEARCH_2510, "exhaustive + random search 2026-10-25 (l20-search.md; recheck 2026-10-26)"),
    "min-capacity": "exact equivalence argument (ADR-032)",
    "rotated-min": "skill-mapping review 2026-10-25 only; no exhaustive search",
}
NEW_FAMILY_ALT = "400 random inputs per design record (not exhaustive)"

MAPPING = {
    "rotated-min": "flag: `compares_with_lo` attributed to its effect (search_space_boundaries), not its cause",
    "min-capacity": "flag: two equality models non-unique (ADR-032)",
    "pivot-index": "judgement for review: four probes all mapped to range_inclusion (ADR-034)",
    "plus-one": "judgement for review: `adds_at_front` mapped to loop_bounds (ADR-034)",
}


def version(slug: str) -> str:
    """The content version recorded in the problem's regenerated content report."""
    text = (ROOT / "docs/content-reports" / f"{slug}.md").read_text()
    m = re.search(r"Content version: `([0-9a-f]{64})`", text)
    return m.group(1)[:12] if m else "?"


def result(slug: str) -> str:
    text = (ROOT / "docs/content-reports" / f"{slug}.md").read_text()
    m = re.search(r"\* Result: (.*)", text)
    return m.group(1) if m else "?"


def main() -> None:
    rows = []
    for toml in sorted((ROOT / "content/demo").glob("*/problem.toml")):
        spec = tomllib.loads(toml.read_text())
        slug = spec["slug"]
        tests = spec["tests"]
        sample = sum(1 for t in tests if t.get("visibility") == "sample")
        empty = any(re.match(r"^[A-Z] 0\b", t["input"]) for t in tests)
        large = sum(1 for t in tests if t["key"].startswith("large"))
        columns, ref, stats = report(slug)
        groups = {k: g for k, (_, g) in stats.items()}
        limited = sorted(m["key"] for m in spec["error_models"] if m.get("known_limitation"))
        by_skill: dict[str, bool] = dict.fromkeys(spec["skills"], False)
        for m in spec["error_models"]:
            reasons = why_not_nameable(columns[m["key"]], ref, *stats[m["key"]])
            if not reasons and not m.get("known_limitation"):
                by_skill[m["skill"]] = True
        declared = sorted(spec.get("positive_only_skills", {}))
        effective = sorted(s for s, ok in by_skill.items() if not ok and s not in declared)
        heldout = len(list((ROOT / "eval/heldout" / slug).glob("*.cpp")))
        if slug in ORIGINAL:
            review = "owner-accepted content and held-out set (CE0/CE1.1)"
        elif slug in UNREVIEWED:
            review = "**Unreviewed** (provisional, owner 2026-10-25 07:50)"
        else:
            review = "bank expansion 2026-10-25; not owner-reviewed for research use"
        lim = []
        if limited:
            lim.append("known_limitation: " + ", ".join(f"`{k}`" for k in limited))
        if declared:
            lim.append("positive-only (declared): " + ", ".join(declared))
        if effective:
            lim.append("positive-only (effective, rules 4b/7/8a): " + ", ".join(effective))
        rows.append(
            [
                f"`{slug}` `{version(slug)}`",
                spec["family"],
                result(slug),
                f"{len(tests)} ({sample} sample, {large} large); empty input {'yes' if empty else 'no'}",
                f"{len(spec['error_models'])} models, groups {min(groups.values())}–{max(groups.values())}; "
                + ALT.get(slug, NEW_FAMILY_ALT),
                "author-defined, unvalidated (L10/L22)"
                + (f"; {MAPPING[slug]}" if slug in MAPPING else ""),
                str(len(spec.get("banned_names", []))),
                review + f"; held-out {heldout} author-written",
                "yes" if spec.get("recommendable", True) else "no",
                "; ".join(lim) or "—",
            ]
        )
    head = [
        "ID and version",
        "Family",
        "Reference / content validation",
        "Contract and edge-case tests",
        "Fingerprints and alternative-cause review",
        "Skill-mapping validity",
        "Banned names",
        "Research review status",
        "Recommendable",
        "Outstanding limitations",
    ]
    print("| " + " | ".join(head) + " |")
    print("| " + " | ".join("---" for _ in head) + " |")
    for r in rows:
        print("| " + " | ".join(r) + " |")


if __name__ == "__main__":
    main()
