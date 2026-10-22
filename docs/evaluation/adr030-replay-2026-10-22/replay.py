"""ADR-030 proposal stage: case-by-case replay of the candidate rule on recorded evidence.

The candidate rule lives in this script only; production code is unchanged and v1.1 and
v1.2 stay selectable (`METHODS["v1.1"]`, `METHODS["v1"]`). For every recorded run of the
held-out, calibration, VAL1-A and VAL1-A2 sets, the recorded observations are diagnosed
with v1.1, v1.2 and the candidate, and the downstream consequences (skill observations,
recommendation, feedback) are computed with the production code. Nothing is re-executed.

Before anything is reported, the replay must reproduce every recorded v1.2 outcome and
model (and v1.1 where it was recorded); the script stops on any difference.

Run from backend/:  uv run python ../docs/evaluation/adr030-replay-2026-10-22/replay.py
Writes cases.json and replay.md next to this script.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
sys.path.insert(0, str(EVAL / "adr027-2026-10-21"))

from consequences import consequences, parse_signature  # noqa: E402

from codeadapt.content.catalogue import Catalogue  # noqa: E402
from codeadapt.diagnosis import METHODS, Diagnosis, DiagnosticInput, Observation, Outcome  # noqa: E402

ROOT = EVAL.parents[1]
A2 = EVAL / "val1a2-2026-10-22"
VAL1A = EVAL / "val1a-2026-10-21/results"
CANDIDATE_VERSION = "1.3-candidate"


def candidate(data: DiagnosticInput) -> Diagnosis:
    """v1.2, then ADR-030: a name resting on uninformative evidence becomes
    `insufficient_evidence` (rule 8a: the named model's fingerprint is constant; rule 8b: a
    test where the named model differs from the reference was excluded)."""
    d = METHODS["v1"].diagnose(data)
    if d.outcome is not Outcome.HYPOTHESIS_SUPPORTED:
        return d
    model = d.selected_model
    assert model is not None
    prediction = data.models[model]
    reasons = []
    if len(set(prediction.values())) == 1:
        reasons.append("8a")
    thinned = sorted(
        o.test_key
        for o in data.observations
        if o.excluded_reason is not None and prediction[o.test_key] != data.reference[o.test_key]
    )
    if thinned:
        reasons.append("8b")
    if not reasons:
        return d
    rationale = dict(d.rationale)
    rationale["rule"] = reasons[0]
    rationale["uninformative"] = reasons
    rationale["consistent_model"] = model
    rationale["informative_tests_excluded"] = thinned
    for key in ("caveat", "evidence_strength", "qualification"):
        rationale.pop(key, None)
    return Diagnosis(
        method=d.method,
        method_version=CANDIDATE_VERSION,
        outcome=Outcome.INSUFFICIENT_EVIDENCE,
        candidates=d.candidates,
        support=d.support,
        rationale=rationale,
    )


def fingerprints() -> dict[str, tuple[dict, dict]]:
    out = {}
    envs = {"lower-bound": VAL1A / "pipeline-environment.json"}
    envs |= {p: A2 / f"results/{p}-environment.json" for p in ("count-occurrences", "last-less-than", "first-true")}
    for slug, path in envs.items():
        env = json.loads(path.read_text())
        ref = {k: parse_signature(v) for k, v in env["reference"].items()}
        models = {m: {k: parse_signature(v) for k, v in p.items()} for m, p in env["models"].items()}
        out[slug] = (env["content_version"], ref, models)
    return out


def summary(d: Diagnosis, problem: Any, problems: dict) -> dict:
    # consequences() picks policy 1.4 for method 1.2; the candidate's outcomes are all
    # ones policy 1.4 already handles, so its diagnoses are evaluated under 1.4 too.
    probe = d.model_copy(update={"method_version": "1.2"}) if d.method_version == CANDIDATE_VERSION else d
    c = consequences(probe, problem, problems)
    c["rule"] = d.rationale.get("rule")
    c["uninformative"] = d.rationale.get("uninformative", [])
    return c


def runs_of(record: dict, kind: str) -> list[dict[str, tuple[str, str | None]]]:
    if kind == "heldout":
        return [{k: (v[0], v[1]) for k, v in run.items()} for run in record["observations"]]
    if kind == "val1a":
        return [
            {k: (v, run["excluded"].get(k)) for k, v in run["signatures"].items()} for run in record["runs"]
        ]
    return [{k: (v[0], v[1]) for k, v in run["observations"].items()} for run in record["runs"]]


def main() -> None:
    catalogue = Catalogue.load(ROOT / "content/demo")
    problems = {p.spec.slug: p.spec for p in catalogue.problems}
    fps = fingerprints()
    for slug, (version, _, _) in fps.items():
        if catalogue.by_slug[slug].version != version:
            sys.exit(f"{slug}: content version changed since the recorded runs")

    sources: list[tuple[str, str, str, dict, dict]] = []  # set, problem, case, record, expected
    for r in json.loads((EVAL / "adr027-2026-10-21/heldout-calibration.json").read_text()):
        slug, _, name = r["case"].partition("/")
        expected = {m: (r[m]["outcome"], r[m]["selected_model"]) for m in ("v1.1", "v1.2")}
        sources.append((r["set"], slug, name, r, expected | {"truth": r["truth"], "kind": "heldout"}))
    lb_labels = json.loads((A2 / "results/lower-bound-behaviour-labels.json").read_text())
    lb_cases = {c["id"]: c for c in json.loads((VAL1A / "cases.json").read_text())}
    for line in (VAL1A / "pipeline.jsonl").read_text().splitlines():
        r = json.loads(line)
        first = r["runs"][0]
        lab = lb_labels[r["program"]]
        truth = lab["label"]
        sources.append(
            (
                "val1a",
                "lower-bound",
                r["program"],
                r,
                {
                    "v1.1": (first["outcome"], first["selected_model"]),
                    "truth": truth,
                    "matches": lab["matches"],
                    "category": lb_cases.get(r["program"], {}).get("category", "original"),
                    "kind": "val1a",
                },
            )
        )
    a2_cases = {
        (c["problem"], c["id"]): c for c in json.loads((A2 / "results/cases.json").read_text())
    }
    for slug in ("count-occurrences", "last-less-than", "first-true"):
        labels = json.loads((ROOT / f"eval/mutation/{slug}/behaviour_labels.json").read_text())
        second = {
            r["program"]: r["runs"]
            for r in map(json.loads, (A2 / f"results/{slug}.run2.jsonl").read_text().splitlines())
        }
        for line in (A2 / f"results/{slug}.jsonl").read_text().splitlines():
            r = json.loads(line)
            r["runs"] = r["runs"] + second[r["program"]]
            first = r["runs"][0]
            lab = labels[r["program"]]
            sources.append(
                (
                    "val1a2",
                    slug,
                    r["program"],
                    r,
                    {
                        "v1.1": (first["v1.1"]["outcome"], first["v1.1"]["selected_model"]),
                        "v1.2": (first["v1.2"]["outcome"], first["v1.2"]["selected_model"]),
                        "truth": lab["label"],
                        "matches": lab["matches"],
                        "category": a2_cases.get((slug, r["program"]), {}).get("category", "original"),
                        "kind": "val1a2",
                    },
                )
            )

    rows = []
    for set_name, slug, name, record, exp in sources:
        version, reference, models = fps[slug]
        problem = catalogue.by_slug[slug]
        per: dict[str, list[dict]] = {"v1.1": [], "v1.2": [], "candidate": []}
        for i, run in enumerate(runs_of(record, exp["kind"])):
            data = DiagnosticInput(
                problem_version=version,
                compiled=bool(run) or exp.get("category") != "compile_error",
                observations=tuple(
                    Observation(test_key=k, signature=parse_signature(s), excluded_reason=x)
                    for k, (s, x) in run.items()
                ),
                reference=reference,
                models=models,
            )
            if exp["kind"] == "val1a" and record["runs"][i]["outcome"] == "compile_error":
                data = data.model_copy(update={"compiled": False})
            if exp["kind"] == "val1a2" and not record["runs"][i]["compiled"]:
                data = data.model_copy(update={"compiled": False})
            old, new, cand = METHODS["v1.1"].diagnose(data), METHODS["v1"].diagnose(data), candidate(data)
            for m, d in (("v1.1", old), ("v1.2", new)):
                if m in exp and i == 0 and (d.outcome.value, d.selected_model) != tuple(exp[m]):
                    sys.exit(f"{set_name} {slug}/{name}: {m} replay differs from the record")
            per["v1.1"].append(summary(old, problem, problems))
            per["v1.2"].append(summary(new, problem, problems))
            per["candidate"].append(summary(cand, problem, problems))
        rows.append(
            {
                "set": set_name,
                "problem": slug,
                "case": name,
                "truth": exp["truth"],
                "matches": exp.get("matches"),
                "category": exp.get("category"),
                "reproducible": all(r == per["candidate"][0] for r in per["candidate"]),
                **{m: v[0] for m, v in per.items()},
            }
        )
    (HERE / "cases.json").write_text(json.dumps(rows, indent=1) + "\n")
    (HERE / "replay.md").write_text(report(rows) + "\n")


def correct(row: dict, model: str | None) -> bool | None:
    if model is None:
        return None
    if row["set"] in ("heldout", "calibration"):
        return model == row["truth"]
    return f"model:{model}" in (row["matches"] or [])


def report(rows: list[dict]) -> str:
    md = ["# ADR-030 replay: v1.1, v1.2 and the candidate rule, case by case", ""]
    md += [
        "Recorded evidence only; nothing re-executed. Every recorded v1.2 (and v1.1) outcome and",
        "model was reproduced before these numbers were computed. Synthetic and author-written",
        "cases only: not real-student evidence.",
        "",
        "## Summary",
        "",
        "| Set | Scored programs | Method | Named | Named correctly | Wrong names | `incorrect` skill observations on a wrong skill |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for set_name in ("heldout", "calibration", "val1a", "val1a2"):
        sel = [r for r in rows if r["set"] == set_name and r["category"] in (None, "incorrect_failing")]
        sel = [r for r in sel if r["truth"] not in ("correct", "reference")]
        for m in ("v1.1", "v1.2", "candidate"):
            named = [r for r in sel if r[m]["outcome"] == "hypothesis_supported"]
            right = [r for r in named if correct(r, r[m]["selected_model"])]
            wrong_skill = sum(
                any(o.endswith(":incorrect") for o in r[m]["skill_observations"]) for r in named if r not in right
            )
            md.append(
                f"| {set_name} | {len(sel)} | {m} | {len(named)} | {len(right)} | {len(named) - len(right)} | {wrong_skill} |"
            )
    md += ["", "Scored programs: incorrect programs only (held-out and calibration: every case whose truth is", "not `correct`; VAL1-A/A2: `incorrect_failing`). Correctness: held-out/calibration against the", "author's truth label; VAL1-A/A2 against the behavioural label (PLAN.md §4 of VAL1-A2).", ""]
    changed = [r for r in rows if (r["v1.2"]["outcome"], r["v1.2"]["selected_model"]) != (r["candidate"]["outcome"], r["candidate"]["selected_model"])]
    md += ["## Every case the candidate changes (v1.2 → candidate)", ""]
    md += ["| Set | Case | Truth / label | v1.2 name | Was it right? | Rule | Feedback after | Skill observations after |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in changed:
        md.append(
            f"| {r['set']} | {r['problem']}/{r['case']} | {r['truth']} | {r['v1.2']['selected_model']} | "
            f"{'yes' if correct(r, r['v1.2']['selected_model']) else 'no'} | {','.join(r['candidate']['uninformative'])} | "
            f"{r['candidate']['feedback']['kind']} | {', '.join(r['candidate']['skill_observations']) or 'none'} |"
        )
    other = [
        r for r in rows
        if r not in changed and any(r["v1.2"][k] != r["candidate"][k] for k in ("skill_observations", "recommendation", "feedback"))
    ]
    md += ["", f"Cases whose diagnosis is unchanged but whose consequences differ: {len(other)}.", ""]
    counts = Counter((r["set"], tuple(r["candidate"]["uninformative"])) for r in changed)
    md += ["Changed cases by set and rule: " + ", ".join(f"{s} {'+'.join(k)}: {n}" for (s, k), n in sorted(counts.items())), ""]
    nonrep = [f"{r['set']}/{r['problem']}/{r['case']}" for r in rows if not r["reproducible"]]
    md += [f"Programs whose candidate result differs between runs: {len(nonrep)} {nonrep}"]
    return "\n".join(md)


if __name__ == "__main__":
    main()
