"""VAL1-A2 analysis (PLAN.md §6–§8) over the raw pipeline records, the behavioural labels and
the native symptom counts. Also scores VAL1-A's lower-bound mutants, as replayed under v1.2
in ../adr027-2026-10-21/val1a.json, against their behavioural labels (four-problem pool).

Run from backend/:  uv run python ../docs/evaluation/val1a2-2026-10-22/analyse.py
Writes results/summary.json and results/tables.md. Reads only; changes nothing else.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from codeadapt.content import load_catalogue

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RES = HERE / "results"
PROBLEMS = ("count-occurrences", "last-less-than", "first-true")
STYLES = {"A": "half-open (reference style)", "B": "closed + answer variable", "C": "recursive"}
OUTCOMES = (
    "hypothesis_supported",
    "non_termination_observed",
    "ambiguous",
    "insufficient_evidence",
    "unmodelled_behaviour",
)
COARSE = ("runtime_error", "memory_limit")

SPECS = {p.spec.slug: p.spec for p in load_catalogue(ROOT / "content/demo")}
SKILL = {s: {m.key: m.skill for m in SPECS[s].error_models} for s in SPECS}
LIMITED = {s: {m.key for m in SPECS[s].error_models if m.known_limitation} for s in SPECS}


def interval(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def rate(k: int, n: int) -> dict:
    lo, hi = interval(k, n)
    return {"k": k, "n": n, "p": k / n if n else None, "lo": lo, "hi": hi}


def fmt(r: dict) -> str:
    if not r["n"]:
        return f"{r['k']}/0 (n/a)"
    return f"{r['k']}/{r['n']} ({100 * r['p']:.0f}%, CI {100 * r['lo']:.0f}–{100 * r['hi']:.0f}%)"


def judge(slug: str, model: str | None, matches: list[str]) -> dict:
    """Behavioural verdict on a named diagnosis (PLAN.md §4, §7)."""
    if model is None:
        return {}
    keys = [m.split(":", 1)[1] for m in matches if m.startswith("model:")]
    correct = model in keys
    same_skill = any(SKILL[slug][k] == SKILL[slug][model] for k in keys)
    return {"correct": correct, "cross_skill": not correct and not same_skill}


def audit_cases(slug: str) -> list[dict]:
    manifest = {e["id"]: e for e in json.loads((ROOT / f"eval/mutation/{slug}/manifest.json").read_text())}
    labels = json.loads((ROOT / f"eval/mutation/{slug}/behaviour_labels.json").read_text())
    symptoms = RES / "native-symptoms.json"
    native = json.loads(symptoms.read_text())[slug] if symptoms.exists() else {}
    env = json.loads((RES / f"{slug}-environment.json").read_text())
    rows = [json.loads(x) for x in (RES / f"{slug}.jsonl").read_text().splitlines() if x]
    run2 = RES / f"{slug}.run2.jsonl"
    if run2.exists():
        second = {r["program"]: r["runs"] for r in map(json.loads, run2.read_text().splitlines()) if r}
        for row in rows:
            row["runs"] += second.get(row["program"], [])
    cases = []
    for row in rows:
        name = row["program"]
        runs = row["runs"]
        first = runs[0]
        d, old = first["v1.2"], first["v1.1"]
        reproducible = all(
            (r["v1.2"]["outcome"], r["v1.2"]["selected_model"], r["observations"])
            == (d["outcome"], d["selected_model"], first["observations"])
            for r in runs
        )
        lab = labels[name]
        if not first["compiled"] or d["outcome"] == "compile_error":
            cat = "compile_error"
        elif d["outcome"] in ("execution_error", "unreliable_evidence") or not reproducible:
            cat = "unreliable"
        elif d["outcome"] == "no_failure_observed":
            cat = "equivalent" if lab["label"] == "reference" else "suite_gap"
        else:
            cat = "incorrect_failing"
        obs = first["observations"]
        reliable = {k: v[0] for k, v in obs.items() if v[1] is None}
        entry = manifest.get(name, {})
        # Does the pipeline's reliable evidence agree with the native behavioural label? Labels
        # were computed at -O1 (PLAN.md §5); the pipeline builds at -O2, so programs whose
        # behaviour depends on undefined behaviour can differ.
        expected = [env["reference"]] if lab["label"] == "reference" else []
        expected += [env["models"][m.split(":", 1)[1]] for m in lab["matches"] if m.startswith("model:")]
        label_consistent = (
            None
            if cat in ("compile_error", "unreliable") or lab["label"] in ("none", "compile_error")
            else any(all(fp.get(k) == v for k, v in reliable.items()) for fp in expected)
        )
        named = d["selected_model"]
        fp = env["models"].get(named or "", {})
        cases.append(
            {
                "problem": slug,
                "named_fingerprint_constant": bool(fp) and len(set(fp.values())) == 1,
                "evidence_equals_named_fingerprint": bool(fp)
                and all(fp.get(k) == v for k, v in reliable.items()),
                "id": name,
                "original": name.startswith("original:"),
                "style": entry.get("style") or {"half_open": "A", "closed_answer": "B", "recursive": "C"}[
                    name.split(":", 1)[1]
                ],
                "operator": entry.get("operator"),
                "line": entry.get("original_line"),
                "mutated": entry.get("mutated_line"),
                "category": cat,
                "reproducible": reproducible,
                "label_consistent": label_consistent,
                "runs": len(runs),
                "label": lab["label"],
                "matches": lab["matches"],
                "v1.2": d | judge(slug, d["selected_model"], lab["matches"]),
                "v1.1": old | judge(slug, old["selected_model"], lab["matches"]),
                "qualified": d["outcome"] == "hypothesis_supported"
                and (d["evidence_strength"] == "single_behaviour" or d["selected_model"] in LIMITED[slug]),
                "qualified_v1.1": old["outcome"] == "hypothesis_supported"
                and (old["evidence_strength"] == "single_behaviour" or old["selected_model"] in LIMITED[slug]),
                "coarse_tests": sorted(k for k, s in reliable.items() if s.split(":")[0] in COARSE),
                "time_limit_tests": sorted(k for k, s in reliable.items() if s.startswith("time_limit")),
                "excluded": {k: v[1] for k, v in obs.items() if v[1] is not None},
                "supporting_kinds": sorted({reliable[k].split(":")[0] for k in d["supporting_tests"] if k in reliable}),
                "signature_vector": [obs[k][0] for k in sorted(obs)],
                "native": native.get(name, {}),
            }
        )
    return cases


def lower_bound_cases() -> list[dict]:
    """VAL1-A's recorded evidence as replayed under v1.2, with behavioural labels."""
    replay = json.loads((HERE.parent / "adr027-2026-10-21/val1a.json").read_text())
    labels = json.loads((RES / "lower-bound-behaviour-labels.json").read_text())
    recorded = {
        c["id"]: c for c in json.loads((HERE.parent / "val1a-2026-10-21/results/cases.json").read_text())
    }
    cases = []
    for r in replay:
        name = r["case"]
        lab = labels[name]
        cat = r["category"]
        if cat == "original":
            continue
        d, old = r["v1.2"], r["v1.1"]
        cases.append(
            {
                "problem": "lower-bound",
                "id": name,
                "style": recorded[name]["style"],
                "category": cat,
                "label": lab["label"],
                "matches": lab["matches"],
                "concept_label_strict": recorded[name]["label_strict"],
                "v1.2": d | judge("lower-bound", d["selected_model"], lab["matches"]),
                "v1.1": old | judge("lower-bound", old["selected_model"], lab["matches"]),
                "qualified": d["outcome"] == "hypothesis_supported"
                and (d["evidence_strength"] == "single_behaviour" or d["known_limitation"]),
                "qualified_v1.1": old["outcome"] == "hypothesis_supported"
                and (old["evidence_strength"] == "single_behaviour" or old["known_limitation"]),
            }
        )
    return cases


def block(sel: list[dict], method: str = "v1.2") -> dict:
    cat = Counter(c["category"] for c in sel)
    inc = [c for c in sel if c["category"] == "incorrect_failing"]
    named = [c for c in inc if c[method]["outcome"] == "hypothesis_supported"]
    qkey = "qualified" if method == "v1.2" else "qualified_v1.1"
    unq = [c for c in named if not c[qkey]]
    qual = [c for c in named if c[qkey]]
    wrong = [c for c in named if not c[method]["correct"]]
    return {
        "programs": len(sel),
        "categories": dict(sorted(cat.items())),
        "outcomes": dict(Counter(c[method]["outcome"] for c in inc)),
        "named_coverage": rate(len(named), len(inc)),
        "symptom_rate": rate(sum(c[method]["outcome"] == "non_termination_observed" for c in inc), len(inc)),
        "wrong_name": rate(len(wrong), len(named)),
        "wrong_name_unqualified": rate(sum(not c[method]["correct"] for c in unq), len(unq)),
        "wrong_name_qualified": rate(sum(not c[method]["correct"] for c in qual), len(qual)),
        "cross_skill_unqualified": [c["problem"] + "/" + c["id"] for c in unq if c[method].get("cross_skill")],
        "wrong": [
            {
                "case": c["problem"] + "/" + c["id"],
                "named": c[method]["selected_model"],
                "label": c["label"],
                "qualified": c[qkey],
                "cross_skill": c[method]["cross_skill"],
                "supporting_kinds": c.get("supporting_kinds"),
            }
            for c in wrong
        ],
        "suite_gap": rate(cat["suite_gap"], cat["suite_gap"] + cat["incorrect_failing"]),
    }


def recall(sel: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for c in sel:
        if c["category"] != "incorrect_failing":
            continue
        for m in c["matches"]:
            if not m.startswith("model:"):
                continue
            key = f"{c['problem']}/{m.split(':', 1)[1]}"
            r = out.setdefault(key, {"labelled": 0, "diagnosed_as_it": 0})
            r["labelled"] += 1
            r["diagnosed_as_it"] += c["v1.2"]["selected_model"] == m.split(":", 1)[1]
    return dict(sorted(out.items()))


def collisions(sel: list[dict]) -> dict:
    by_model: dict[str, list[dict]] = defaultdict(list)
    for c in sel:
        if c["category"] == "incorrect_failing" and c["v1.2"]["outcome"] == "hypothesis_supported":
            by_model[f"{c['problem']}/{c['v1.2']['selected_model']}"].append(c)
    groups: dict[tuple, set] = defaultdict(set)
    members: dict[tuple, list] = defaultdict(list)
    for c in sel:
        if c["category"] == "incorrect_failing" and "signature_vector" in c:
            key = (c["problem"], tuple(c["signature_vector"]))
            groups[key].add(c["label"])
            members[key].append(c["id"])
    return {
        "per_named_model": {
            m: {"mutants": len(cs), "distinct_labels": sorted({c["label"] for c in cs})}
            for m, cs in sorted(by_model.items())
        },
        "same_signatures_different_labels": [
            {"problem": k[0], "mutants": members[k], "labels": sorted(v)}
            for k, v in groups.items()
            if len(v) > 1
        ],
    }


def coarse(sel: list[dict]) -> dict:
    inc = [c for c in sel if c["category"] == "incorrect_failing"]
    named = [c for c in inc if c["v1.2"]["outcome"] == "hypothesis_supported"]
    only = [c for c in named if c["supporting_kinds"] and set(c["supporting_kinds"]) <= set(COARSE)]
    excluded = Counter(r for c in sel for r in set(c["excluded"].values()))
    compiled = [c for c in sel if c["native"].get("compiled") and c["category"] != "compile_error"]
    cross = Counter()
    for c in compiled:
        cross[("TLE" if c["native"]["tle"] else "-", "time_limit" if c["time_limit_tests"] else "-")] += 1
        cross[("CRASH" if c["native"]["crash"] else "-", "coarse" if c["coarse_tests"] else "-")] += 1
    return {
        "programs_with_reliable_runtime_error_or_memory_limit": sum(bool(c["coarse_tests"]) for c in sel),
        "incorrect_failing_with_them": sum(bool(c["coarse_tests"]) for c in inc),
        "programs_with_any_exclusion_by_reason": dict(sorted(excluded.items())),
        "named_supported_only_by_coarse": rate(len(only), len(named)),
        "wrong_among_coarse_only": rate(sum(not c["v1.2"]["correct"] for c in only), len(only)),
        "coarse_only_cases": [c["problem"] + "/" + c["id"] for c in only],
        "native_vs_pipeline": {f"{a} / {b}": n for (a, b), n in sorted(cross.items())},
    }


def readings(pool: dict, by_style: dict, coarse_pool: dict) -> dict:
    named = pool["named_coverage"]["k"]
    wrong = pool["wrong_name"]
    a, bc = by_style["A"]["named_coverage"], by_style["B+C"]["named_coverage"]
    return {
        "G0_precision_not_evaluable": named < 10,
        "G1_wrong_name_generalises": None if named < 10 else (wrong["p"] >= 0.10 or wrong["hi"] >= 0.20),
        "G1_note": "evaluated only if G0 is false; an unevaluable precision is never a pass",
        "G1b_unqualified_cross_skill": pool["cross_skill_unqualified"],
        "G2_low_coverage": pool["named_coverage"]["p"] is not None and pool["named_coverage"]["p"] < 0.20,
        "G3_style_dependence": a["p"] is not None and bc["p"] is not None and bc["p"] < a["p"] / 2,
        "G4_suite_gap": pool["suite_gap"]["p"] is not None and pool["suite_gap"]["p"] > 0.10,
        "G5_coarse_signature_wrong_name": [
            w["case"] for w in pool["wrong"] if w["supporting_kinds"] and set(w["supporting_kinds"]) <= set(COARSE)
        ],
        "coarse_only_named": coarse_pool["named_supported_only_by_coarse"],
    }


def main() -> None:
    cases = {s: audit_cases(s) for s in PROBLEMS}
    originals = {s: [c for c in cs if c["original"]] for s, cs in cases.items()}
    mutants = {s: [c for c in cs if not c["original"]] for s, cs in cases.items()}
    pooled = [c for s in PROBLEMS for c in mutants[s]]
    lb = lower_bound_cases()
    lb_check = [
        c["id"]
        for c in lb
        if (c["category"] == "equivalent") != (c["label"] == "reference") and c["category"] != "unreliable"
    ]
    by_style = {st: block([c for c in pooled if c["style"] == st]) for st in STYLES}
    by_style["B+C"] = block([c for c in pooled if c["style"] in "BC"])
    pool = block(pooled)
    cp = coarse(pooled)
    summary = {
        "runs_per_program": dict(Counter(c["runs"] for cs in cases.values() for c in cs)),
        "data": "synthetic single-edit mutants; behavioural labels computed natively; not real-student evidence",
        "originals": {
            s: {c["id"]: (c["category"], c["v1.2"]["outcome"]) for c in originals[s]} for s in PROBLEMS
        },
        "per_problem": {s: block(mutants[s]) for s in PROBLEMS},
        "per_problem_style": {
            s: {st: block([c for c in mutants[s] if c["style"] == st]) for st in STYLES} for s in PROBLEMS
        },
        "pooled": pool,
        "pooled_by_style": by_style,
        "pooled_v1.1": block(pooled, "v1.1"),
        "per_problem_v1.1": {s: block(mutants[s], "v1.1") for s in PROBLEMS},
        "recall": recall(pooled),
        "collisions": collisions(pooled),
        "coarse": cp,
        "coarse_per_problem": {s: coarse(mutants[s]) for s in PROBLEMS},
        "readings": readings(pool, by_style, cp),
        "exploratory_wrong_names": [
            {"case": c["problem"] + "/" + c["id"], "named": c["v1.2"]["selected_model"],
             "named_fingerprint_constant": c["named_fingerprint_constant"],
             "evidence_equals_named_fingerprint": c["evidence_equals_named_fingerprint"]}
            for c in pooled
            if c["category"] == "incorrect_failing" and c["v1.2"].get("correct") is False
        ],
        "label_pipeline_disagreements": [
            {"case": c["problem"] + "/" + c["id"], "label": c["label"], "category": c["category"],
             "v1.2": c["v1.2"]["outcome"], "model": c["v1.2"]["selected_model"]}
            for c in pooled
            if c["label_consistent"] is False
        ],
        "lower_bound_replay": {
            "v1.2": block(lb),
            "v1.1": block(lb, "v1.1"),
            "by_style": {st: block([c for c in lb if c["style"] == st]) for st in STYLES},
            "label_vs_recorded_equivalence_disagreements": lb_check,
            "recall": recall(lb),
        },
        "four_problem_pool": {"v1.2": block(pooled + lb), "v1.1": block(pooled + lb, "v1.1")},
    }
    (RES / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    (RES / "cases.json").write_text(json.dumps(pooled + lb, indent=1, sort_keys=True) + "\n")
    (RES / "tables.md").write_text(tables(summary, pooled) + "\n")


def tables(s: dict, pooled: list[dict]) -> str:
    md: list[str] = []
    P = md.append
    P("# VAL1-A2 tables (generated by analyse.py; do not edit)\n")
    P("Synthetic single-edit mutants. Behavioural labels, not human labels. Not real-student evidence.\n")
    P(f"Runs per program: {s['runs_per_program']} (reproducibility is checked only where 2 runs exist).\n")
    P("## Originals\n")
    for slug, o in s["originals"].items():
        P(f"- {slug}: " + ", ".join(f"{k} → {v[1]}" for k, v in o.items()))
    P("\n## Main metrics, method 1.2\n")
    P("| Set | Programs | Incorrect-failing | Named coverage | Symptom rate | Wrong name | Suite gap |")
    P("| --- | --- | --- | --- | --- | --- | --- |")

    def row(name: str, b: dict) -> None:
        P(
            f"| {name} | {b['programs']} | {b['categories'].get('incorrect_failing', 0)} | "
            f"{fmt(b['named_coverage'])} | {fmt(b['symptom_rate'])} | {fmt(b['wrong_name'])} | {fmt(b['suite_gap'])} |"
        )

    for slug, b in s["per_problem"].items():
        row(slug, b)
    row("**Pooled (3 problems)**", s["pooled"])
    for st, b in s["pooled_by_style"].items():
        row(f"Pooled style {st}", b)
    row("lower-bound (VAL1-A replay)", s["lower_bound_replay"]["v1.2"])
    row("**Four-problem pool**", s["four_problem_pool"]["v1.2"])
    P("\n## Per problem and style, method 1.2\n")
    P("| Problem | Style | Programs | Categories | Named coverage | Wrong name |")
    P("| --- | --- | --- | --- | --- | --- |")
    for slug, styles in s["per_problem_style"].items():
        for st, b in styles.items():
            P(
                f"| {slug} | {st} | {b['programs']} | {b['categories']} | "
                f"{fmt(b['named_coverage'])} | {fmt(b['wrong_name'])} |"
            )
    P("\n## Outcomes of incorrect-failing mutants, method 1.2\n")
    P("| Problem | " + " | ".join(OUTCOMES) + " |")
    P("| --- |" + " --- |" * len(OUTCOMES))
    for slug, b in s["per_problem"].items():
        P(f"| {slug} | " + " | ".join(str(b["outcomes"].get(o, 0)) for o in OUTCOMES) + " |")
    P("\n## Precision split, method 1.2 (pooled 3 problems)\n")
    p = s["pooled"]
    P(f"- Unqualified: wrong {fmt(p['wrong_name_unqualified'])}")
    P(f"- Qualified: wrong {fmt(p['wrong_name_qualified'])}")
    P(f"- Unqualified cross-skill wrong names (G1b): {p['cross_skill_unqualified'] or 'none'}")
    P("\n### Every wrong name\n")
    P("| Case | Named | Behavioural label | Qualified | Cross-skill | Supporting signature kinds |")
    P("| --- | --- | --- | --- | --- | --- |")
    for w in p["wrong"]:
        P(
            f"| {w['case']} | {w['named']} | {w['label']} | {w['qualified']} | {w['cross_skill']} | "
            f"{', '.join(w['supporting_kinds'] or [])} |"
        )
    P("\n## Every named diagnosis (pooled 3 problems)\n")
    P("| Case | Edit | Named | Qualified | Behavioural label | Correct |")
    P("| --- | --- | --- | --- | --- | --- |")
    for c in pooled:
        if c["category"] == "incorrect_failing" and c["v1.2"]["outcome"] == "hypothesis_supported":
            P(
                f"| {c['problem']}/{c['id']} | `{c['line']}` → `{c['mutated']}` | {c['v1.2']['selected_model']} | "
                f"{c['qualified']} | {c['label']} | {c['v1.2']['correct']} |"
            )
    P("\n## Library recall (incorrect-failing mutants behaving as a model)\n")
    P("| Model | Labelled | Diagnosed as it |")
    P("| --- | --- | --- |")
    for m, r in s["recall"].items():
        P(f"| {m} | {r['labelled']} | {r['diagnosed_as_it']} |")
    P("\n## Collisions\n")
    for m, r in s["collisions"]["per_named_model"].items():
        P(f"- {m}: {r['mutants']} mutants, labels {r['distinct_labels']}")
    same = s["collisions"]["same_signatures_different_labels"]
    P(f"\nGroups with identical signature vectors but different behavioural labels: {len(same)}")
    for g in same:
        P(f"- {g['problem']}: {', '.join(g['mutants'])} → {g['labels']}")
    P("\n## Coarse signatures (ADR-027 Q3)\n")
    c = s["coarse"]
    P(f"- Programs with a reliable runtime_error or memory_limit observation: {c['programs_with_reliable_runtime_error_or_memory_limit']}"
      f" ({c['incorrect_failing_with_them']} incorrect-failing)")
    P(f"- Programs with an excluded observation, by reason: {c['programs_with_any_exclusion_by_reason']}")
    P(f"- Named diagnoses supported only by runtime_error/memory_limit: {fmt(c['named_supported_only_by_coarse'])}")
    P(f"- Wrong among those: {fmt(c['wrong_among_coarse_only'])} {c['coarse_only_cases']}")
    P(f"- Native symptom vs pipeline signature (native / pipeline): {c['native_vs_pipeline']}")
    ex = s["exploratory_wrong_names"]
    P("\n## Exploratory (not pre-registered): why the wrong names happen\n")
    P(f"- Wrong names whose reliable evidence equals the named model's fingerprint on every test: "
      f"{sum(e['evidence_equals_named_fingerprint'] for e in ex)}/{len(ex)}")
    P(f"- Wrong names whose named model has a constant fingerprint (same signature on every test): "
      f"{sum(e['named_fingerprint_constant'] for e in ex)}/{len(ex)}")
    dis = s["label_pipeline_disagreements"]
    P("\n## Native label vs pipeline evidence\n")
    P("Labels were computed at -O1 (PLAN.md §5); the pipeline builds at -O2. A labelled-reference or")
    P("labelled-model mutant whose reliable pipeline evidence differs from that program's fingerprint")
    P(f"is listed here ({len(dis)}):\n")
    for d in dis:
        P(f"- {d['case']}: label {d['label']}, {d['category']}, v1.2 {d['v1.2']} {d['model'] or ''}")
    P("\n## Secondary: method 1.1 on the same evidence\n")
    P("| Set | Named coverage | Wrong name |")
    P("| --- | --- | --- |")
    for slug, b in s["per_problem_v1.1"].items():
        P(f"| {slug} | {fmt(b['named_coverage'])} | {fmt(b['wrong_name'])} |")
    P(f"| Pooled (3 problems) | {fmt(s['pooled_v1.1']['named_coverage'])} | {fmt(s['pooled_v1.1']['wrong_name'])} |")
    lb = s["lower_bound_replay"]["v1.1"]
    P(f"| lower-bound (replay) | {fmt(lb['named_coverage'])} | {fmt(lb['wrong_name'])} |")
    fp = s["four_problem_pool"]["v1.1"]
    P(f"| Four-problem pool | {fmt(fp['named_coverage'])} | {fmt(fp['wrong_name'])} |")
    P("\n## Pre-registered readings (pooled 3 problems, method 1.2)\n")
    for k, v in s["readings"].items():
        P(f"- **{k}**: {v}")
    dis = s["lower_bound_replay"]["label_vs_recorded_equivalence_disagreements"]
    P(f"\nLower-bound behavioural label vs VAL1-A recorded equivalence, disagreements: {dis or 'none'}")
    return "\n".join(md)


if __name__ == "__main__":
    main()
