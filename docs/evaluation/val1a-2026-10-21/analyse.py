"""VAL1-A analysis (PLAN.md §6–§8) over results/pipeline.jsonl, results/equivalence.json and
the a-priori labels. Writes results/summary.json and results/tables.md.

Run from backend/:  uv run python ../docs/evaluation/val1a-2026-10-21/analyse.py
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from codeadapt.content import load_catalogue

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / "eval/mutation/lower-bound"
STYLES = {"A": "half-open (reference style)", "B": "closed + answer variable", "C": "recursive"}
ABSTAIN = ("ambiguous", "insufficient_evidence", "unmodelled_behaviour")

spec = next(p.spec for p in load_catalogue(ROOT / "content/demo") if p.spec.slug == "lower-bound")
SKILL = {m.key: m.skill for m in spec.error_models}
LIMITED = {m.key for m in spec.error_models if m.known_limitation}


def wilson(k: int, n: int) -> str:
    if n == 0:
        return f"{k}/0 (n/a)"
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{k}/{n} ({100 * p:.0f}%, 95% CI {100 * max(0, c - h):.0f}–{100 * min(1, c + h):.0f}%)"


def upper(k: int, n: int) -> float:
    if n == 0:
        return 1.0
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    return (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d


def main() -> None:
    manifest = {e["id"]: e for e in json.loads((BASE / "manifest.json").read_text())}
    labels = json.loads((BASE / "labels.json").read_text())
    native = json.loads((HERE / "results/equivalence.json").read_text())
    rows = [json.loads(x) for x in (HERE / "results/pipeline.jsonl").read_text().splitlines() if x]
    pipe = {r["program"]: r for r in rows}

    originals = {k: v["runs"][0]["outcome"] for k, v in pipe.items() if k.startswith("original:")}
    cases = []
    for mid, entry in manifest.items():
        if "excluded" in entry:
            continue
        r = pipe[mid]["runs"]
        first = r[0]
        reproducible = all(
            (x["outcome"], x["selected_model"], x["signatures"])
            == (first["outcome"], first["selected_model"], first["signatures"])
            for x in r
        )
        out = first["outcome"]
        nat = native[mid]["native"]
        if out == "compile_error":
            cat = "compile_error"
        elif out in ("execution_error", "unreliable_evidence") or not reproducible:
            cat = "unreliable"
        elif out == "no_failure_observed":
            cat = "equivalent" if nat == "equivalent" else "suite_gap"
        else:
            cat = "incorrect_failing"
        model = first["selected_model"]
        qualified = out == "hypothesis_supported" and (
            first["evidence_strength"] == "single_behaviour" or model in LIMITED
        )
        lab = labels[mid]
        cases.append(
            {
                "id": mid,
                "style": entry["style"],
                "operator": entry["operator"],
                "edit": entry["edit"],
                "line": entry["original_line"],
                "mutated": entry["mutated_line"],
                "category": cat,
                "outcome": out,
                "model": model,
                "candidates": first["candidates"],
                "qualified": qualified,
                "support_behaviours": first["support_behaviours"],
                "excluded": first["excluded"],
                "reproducible": reproducible,
                "native": nat,
                "native_first_diff": native[mid].get("first_diff_input"),
                "label_strict": lab["strict"],
                "label_lenient": lab["lenient"],
                "debatable": lab["debatable"],
                "signature_vector": [first["signatures"].get(k) for k in sorted(first["signatures"])],
            }
        )

    md: list[str] = []
    summary: dict = {"originals": originals}
    P = md.append

    def block(title: str, sel: list[dict]) -> dict:
        cat = Counter(c["category"] for c in sel)
        inc = [c for c in sel if c["category"] == "incorrect_failing"]
        diag = [c for c in inc if c["outcome"] == "hypothesis_supported"]
        unq = [c for c in diag if not c["qualified"]]
        res: dict = {"programs": len(sel), "categories": dict(cat)}
        P(f"### {title}\n")
        P("| Category | Count |\n| --- | ---: |")
        for k in ("compile_error", "unreliable", "equivalent", "suite_gap", "incorrect_failing"):
            P(f"| {k} | {cat.get(k, 0)} |")
        P(f"| **total** | {len(sel)} |\n")
        P("| Metric (denominator: `incorrect_failing` unless stated) | Value |\n| --- | --- |")
        P(f"| Coverage: diagnosed (any) | {wilson(len(diag), len(inc))} |")
        P(f"| — diagnosed, unqualified | {wilson(len(unq), len(inc))} |")
        P(f"| — diagnosed, qualified | {wilson(len(diag) - len(unq), len(inc))} |")
        for o in ABSTAIN:
            P(f"| Abstained: {o} | {wilson(sum(c['outcome'] == o for c in inc), len(inc))} |")
        res["coverage"] = [len(diag), len(inc)]
        for mode in ("strict", "lenient"):
            agree = [c for c in diag if c["model"] == c[f"label_{mode}"]]
            cross = [c for c in diag if c["model"] != c[f"label_{mode}"]]
            cross_unq = [c for c in cross if not c["qualified"]]
            cross_skill = [
                c for c in cross
                if c[f"label_{mode}"] == "none" or SKILL[c["model"]] != SKILL[c[f"label_{mode}"]]
            ]
            cross_skill_unq = [c for c in cross_skill if not c["qualified"]]
            P(f"| Concept agreement ({mode} labels; denominator: diagnoses) | {wilson(len(agree), len(diag))} |")
            P(f"| Cross-pattern diagnoses ({mode}; denominator: diagnoses) | {wilson(len(cross), len(diag))} |")
            P(f"| — of which unqualified | {len(cross_unq)} |")
            P(f"| — cross-skill, unqualified ({mode}) | {len(cross_skill_unq)} |")
            res[f"cross_{mode}"] = [len(cross), len(diag)]
            res[f"cross_skill_unqualified_{mode}"] = len(cross_skill_unq)
            labelled = [c for c in inc if c[f"label_{mode}"] != "none"]
            hit = [c for c in labelled if c["outcome"] == "hypothesis_supported" and c["model"] == c[f"label_{mode}"]]
            P(f"| Library recall on labelled mutants ({mode}; denominator: labelled `incorrect_failing`) | {wilson(len(hit), len(labelled))} |")
            res[f"recall_{mode}"] = [len(hit), len(labelled)]
        nonequiv = [c for c in sel if c["category"] in ("suite_gap", "incorrect_failing")]
        P(f"| Suite gap (denominator: non-equivalent reliable mutants) | {wilson(cat.get('suite_gap', 0), len(nonequiv))} |")
        res["suite_gap"] = [cat.get("suite_gap", 0), len(nonequiv)]
        lib = sum(c["label_strict"] != "none" for c in sel)
        P(f"| Mutants with a library label (strict; denominator: all mutants) | {wilson(lib, len(sel))} |\n")
        res["library_labelled"] = [lib, len(sel)]
        return res

    P("## Results by style and pooled\n")
    for s, name in STYLES.items():
        summary[s] = block(f"Style {s}: {name}", [c for c in cases if c["style"] == s])
    summary["BC"] = block("Styles B + C pooled", [c for c in cases if c["style"] in "BC"])
    summary["all"] = block("All styles pooled", cases)

    P("## Every diagnosis\n")
    P("| Mutant | Edit | Diagnosed model | Qualified | Groups | Strict label | Lenient label | Agrees (strict) |")
    P("| --- | --- | --- | --- | ---: | --- | --- | --- |")
    for c in cases:
        if c["outcome"] == "hypothesis_supported" and c["category"] == "incorrect_failing":
            P(f"| {c['id']} | `{c['line']}` → `{c['mutated']}` | {c['model']} | {'yes' if c['qualified'] else 'no'} | "
              f"{c['support_behaviours']} | {c['label_strict']} | {c['label_lenient']} | {'yes' if c['model'] == c['label_strict'] else '**no**'} |")
    P("")
    P("## Labelled mutants that were not diagnosed with their label\n")
    P("| Mutant | Edit | Strict label | Category | Outcome | Model / candidates |")
    P("| --- | --- | --- | --- | --- | --- |")
    for c in cases:
        if c["label_strict"] != "none" and not (c["outcome"] == "hypothesis_supported" and c["model"] == c["label_strict"]):
            P(f"| {c['id']} | `{c['line']}` → `{c['mutated']}` | {c['label_strict']} | {c['category']} | {c['outcome']} | "
              f"{c['model'] or ', '.join(c['candidates']) or '—'} |")
    P("")
    P("## Collisions\n")
    by_model: dict[str, list[dict]] = defaultdict(list)
    for c in cases:
        if c["outcome"] == "hypothesis_supported" and c["category"] == "incorrect_failing":
            by_model[c["model"]].append(c)
    P("| Model | Skill | Mutants diagnosed | Distinct strict labels | Styles |")
    P("| --- | --- | ---: | --- | --- |")
    for m in sorted(SKILL):
        cs = by_model.get(m, [])
        labs = Counter(c["label_strict"] for c in cs)
        P(f"| {m} | {SKILL[m]} | {len(cs)} | {', '.join(f'{k} ×{v}' for k, v in sorted(labs.items())) or '—'} | "
          f"{''.join(sorted({c['style'] for c in cs})) or '—'} |")
    sig_groups: dict[tuple, list[str]] = defaultdict(list)
    for c in cases:
        if c["category"] == "incorrect_failing":
            sig_groups[tuple(c["signature_vector"])].append(c["id"])
    multi = {k: v for k, v in sig_groups.items() if len(v) > 1}
    P(f"\nAmong {sum(len(v) for v in sig_groups.values())} `incorrect_failing` mutants there are "
      f"{len(sig_groups)} distinct full signature vectors; {len(multi)} are shared by 2 or more mutants "
      f"({sum(len(v) for v in multi.values())} mutants).\n")
    for v in sorted(multi.values(), key=len, reverse=True):
        P(f"- {', '.join(v)}")
    P("")
    P("## Abstentions on incorrect_failing mutants\n")
    P("| Mutant | Edit | Outcome | Candidates / nearest | Strict label |")
    P("| --- | --- | --- | --- | --- |")
    for c in cases:
        if c["category"] == "incorrect_failing" and c["outcome"] in ABSTAIN:
            r = pipe[c["id"]]["runs"][0]
            near = ", ".join(f"{n['model']}({n['contradicting']})" for n in (r.get("nearest_models") or []))
            P(f"| {c['id']} | `{c['line']}` → `{c['mutated']}` | {c['outcome']} | {', '.join(c['candidates']) or near} | {c['label_strict']} |")
    P("")
    P("## Other categories\n")
    P("| Mutant | Edit | Category | Outcome | Native | Excluded tests |")
    P("| --- | --- | --- | --- | --- | --- |")
    for c in cases:
        if c["category"] != "incorrect_failing":
            ex = "; ".join(f"{k}: {v}" for k, v in sorted(c["excluded"].items())[:3])
            more = f" (+{len(c['excluded']) - 3})" if len(c["excluded"]) > 3 else ""
            P(f"| {c['id']} | `{c['line']}` → `{c['mutated']}` | {c['category']} | {c['outcome']} | {c['native']} | {ex}{more} |")
    P("")
    disagree = [c["id"] for c in cases if c["category"] == "equivalent" and c["native"] != "equivalent"]
    disagree += [c["id"] for c in cases if c["category"] == "incorrect_failing" and c["native"] == "equivalent"]
    summary["native_pipeline_disagreements"] = disagree

    # Thresholds (PLAN.md §8).
    a, bc, al = summary["A"], summary["BC"], summary["all"]
    cov = lambda r: r["coverage"][0] / r["coverage"][1] if r["coverage"][1] else 0.0
    k, n = al["cross_strict"]
    summary["thresholds"] = {
        "T1_cross_pattern": (n > 0 and (k / n >= 0.10 or upper(k, n) >= 0.20)),
        "T1b_unqualified_cross_skill": al["cross_skill_unqualified_strict"],
        "T2_coverage_below_20pct": cov(al) < 0.20,
        "T3_style_bias": cov(bc) < 0.5 * cov(a),
        "T4_suite_gap_above_10pct": al["suite_gap"][1] > 0 and al["suite_gap"][0] / al["suite_gap"][1] > 0.10,
    }
    (HERE / "results/summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    (HERE / "results/cases.json").write_text(json.dumps(cases, indent=1) + "\n")
    (HERE / "results/tables.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"originals": originals, "thresholds": summary["thresholds"],
                      "disagreements": disagree}, indent=1))


if __name__ == "__main__":
    main()
