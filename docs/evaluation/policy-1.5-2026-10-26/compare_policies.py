"""Recommendations of policy versions on fixed synthetic histories (policy 1.5 evaluation).

Run from backend/: `uv run python ../docs/evaluation/policy-1.5-2026-10-26/compare_policies.py
<config> [<config> ...]`, where a config is `<policy version>:<eligibility>` and eligibility is
`e2` (only lower-bound, count-occurrences and last-less-than recommendable, as before
2026-10-26) or `current` (the flags in content/demo). Writes one JSON per config next to this
file and prints summary tables.

Histories (all synthetic, built from the content; no learner data):
- H1, 417 one-attempt histories: for every problem, a pass, each error model named (failing
  the tests it is measured to fail) and each pair of models ambiguous. The set of the
  2026-10-26 recommendability review.
- H2, 286 histories of tests/unit/policy_cases.py over the three original problems: single
  attempts of every rule, each after a pass on another original problem, and all-passed orders.
- H3, sequential trajectories (binary search): start with every unqualified named model of a
  recommendable binary-search problem, then 5 more attempts, each on the recommended problem.
  The simulated learner keeps the same difficulty: if the recommended problem has an error
  model of the targeted skill without a known_limitation, the attempt is diagnosed with it
  (failing the tests it is measured to fail); otherwise the attempt passes. This is a
  deliberately crude stand-in for a learner with a persistent error, not a model of learning.
Results describe which problem a rule picks. They say nothing about whether a pick helps.
"""

from __future__ import annotations

import collections
import inspect
import itertools
import json
import sys
from pathlib import Path

from codeadapt.adaptation import PolicyV1
from codeadapt.content import load_catalogue
from codeadapt.diagnosis import Outcome
from tests.paths import DEMO_CONTENT
from tests.unit.policy_cases import histories as h2_histories
from tests.unit.test_adaptation import attempt

OUT = Path(__file__).parent
CURRENT = {p.spec.slug: p.spec for p in load_catalogue(DEMO_CONTENT)}
ORIGINAL = {"lower-bound", "count-occurrences", "last-less-than"}
E2 = {s: p.model_copy(update={"recommendable": s in ORIGINAL}) for s, p in CURRENT.items()}


def h1(problems):
    for slug, spec in sorted(problems.items()):
        first = spec.tests[0].key
        yield f"{slug}|nofail", [attempt(slug, Outcome.NO_FAILURE_OBSERVED)]
        for m in spec.error_models:
            fail = tuple(t.key for t in spec.tests if m.key in (t.distinguishes or ())) or (first,)
            a = attempt(slug, Outcome.HYPOTHESIS_SUPPORTED, model=m.key, failing=fail)
            yield f"{slug}|named:{m.key}", [a]
        for x, y in itertools.combinations([m.key for m in spec.error_models], 2):
            a = attempt(slug, Outcome.AMBIGUOUS, candidates=(x, y), failing=(first,))
            yield f"{slug}|amb:{x}+{y}", [a]


def h2(problems):
    for i, history in enumerate(h2_histories(problems)):
        yield f"h2-{i:03d}|" + ">".join(f"{a.problem_slug}:{a.outcome.value}" for a in history), history


def h3(policy, problems):
    starts = [
        (spec, m)
        for spec in sorted(problems.values(), key=lambda p: p.slug)
        if spec.family == "binary-search" and spec.recommendable
        for m in spec.error_models
        if not m.known_limitation
    ]
    for spec, m in starts:
        skill = m.skill
        history = [named(spec, m, 0)]
        for n in range(1, 6):
            rec = policy.recommend(history[-1], history, problems)
            if rec.problem_slug is None:
                break
            q = problems[rec.problem_slug]
            same = [x for x in q.error_models if x.skill == skill and not x.known_limitation]
            history.append(named(q, same[0], n) if same else attempt(q.slug, Outcome.NO_FAILURE_OBSERVED, n=n))
        yield f"{spec.slug}:{m.key}", skill, history


def named(spec, m, n):
    fail = tuple(t.key for t in spec.tests if m.key in (t.distinguishes or ())) or (spec.tests[0].key,)
    return attempt(spec.slug, Outcome.HYPOTHESIS_SUPPORTED, n=n, model=m.key, failing=fail)


def trajectories(version: str, eligibility: str) -> None:
    from codeadapt.adaptation import skill_observations

    problems = {"e2": E2, "current": CURRENT}[eligibility]
    policy = PolicyV1(version=version) if "version" in inspect.signature(PolicyV1).parameters else PolicyV1()
    visited, sources, reach, total, firsts = [], [], 0, 0, collections.Counter()
    lines = []
    for key, skill, history in h3(policy, problems):
        total += 1
        path = [a.problem_slug for a in history]
        firsts[path[1] if len(path) > 1 else "-"] += 1
        obs = [o for o in skill_observations(history, problems) if o.skill == skill and o.attempt_ordinal == 1]
        probs = {o.problem_slug for o in obs}
        visited.append(len(set(path)))
        sources.append(len(probs))
        reach += len(obs) >= 3 and len(probs) >= 2
        lines.append(f"  {key} [{skill}]: " + " > ".join(path))
    print(f"\n### policy {version}, eligibility {eligibility} — H3 ({total} trajectories of 6 attempts)")
    print(f"- first follow-up: {dict(firsts.most_common())}")
    print(f"- distinct problems visited per trajectory: mean {sum(visited)/total:.2f}, min {min(visited)}, max {max(visited)}")
    print(f"- distinct problems giving a first-attempt observation of the targeted skill: mean {sum(sources)/total:.2f}")
    print(f"- trajectories reaching >=3 first-attempt observations of the skill from >=2 problems: {reach} of {total}")
    (OUT / f"trajectories-{version}-{eligibility}.txt").write_text("\n".join(lines) + "\n")


def run(version: str, eligibility: str) -> dict[str, dict]:
    problems = {"e2": E2, "current": CURRENT}[eligibility]
    policy = PolicyV1(version=version) if "version" in inspect.signature(PolicyV1).parameters else PolicyV1()
    assert policy.version == version, (policy.version, version)
    out = {}
    for key, history in itertools.chain(h1(problems), h2(problems)):
        r = policy.recommend(history[-1], history, problems)
        again = policy.recommend(history[-1], history, problems)
        out[key] = {
            "rule": r.rule.value,
            "action": r.action.value,
            "problem": r.problem_slug,
            "skills": list(r.target_skills),
            "criterion": None if r.criterion is None else list(r.criterion.skills),
            "flag": r.review_flag,
            "qualified": r.rationale.get("qualified_hypothesis"),
            "repeat": r.problem_slug in {a.problem_slug for a in history} and r.action.value == "new_problem",
            "deterministic": again == r,
        }
    return out


def summary(name: str, res: dict[str, dict], problems) -> None:
    for part in ("H1", "H2"):
        rows = {k: v for k, v in res.items() if k.startswith("h2-") == (part == "H2")}
        acts = collections.Counter(v["action"] for v in rows.values())
        bs = {k: v for k, v in rows.items() if problems[k.split("|")[0].split(":")[0] if part == "H1" else k.split("|")[1].split(">")[-1].split(":")[0]].family == "binary-search"}
        dest = collections.Counter(v["problem"] for v in rows.values() if v["action"] == "new_problem")
        bsdest = collections.Counter(v["problem"] for v in bs.values() if v["action"] == "new_problem")
        skills = collections.Counter(s for v in rows.values() if v["action"] == "new_problem" for s in v["skills"])
        pos_only = sum(
            1 for v in rows.values()
            if v["action"] == "new_problem" and v["rule"] in ("hypothesis_supported", "ambiguous")
            and any(s in problems[v["problem"]].positive_only_skills for s in v["skills"])
        )
        targeted = sum(1 for v in rows.values() if v["action"] == "new_problem" and v["rule"] in ("hypothesis_supported", "ambiguous"))
        no_cand = sum(1 for v in rows.values() if v["action"] == "retry" and v["rule"] in ("hypothesis_supported", "ambiguous", "no_failure_observed"))
        top = max(bsdest.values()) / sum(bsdest.values()) if bsdest else 0
        print(f"\n### {name} — {part} ({len(rows)} histories)")
        print(f"- actions: {dict(sorted(acts.items()))}")
        print(f"- retry because no other candidate (supported/ambiguous/pass): {no_cand}; action none: {acts.get('none', 0)}")
        print(f"- new_problem destinations: {dict(dest.most_common())}")
        print(f"- binary-search destinations: {dict(bsdest.most_common())}; largest share {top:.0%}")
        print(f"- original three picked: {sum(bsdest[s] for s in ORIGINAL)} of {sum(bsdest.values())}")
        print(f"- target skills (new_problem): {dict(skills.most_common())}")
        print(f"- distinct problems picked: {len(dest)}; distinct skills targeted: {len(skills)}")
        print(f"- targeted follow-ups to a problem where a target skill is declared positive-only: {pos_only} of {targeted}")
        print(f"- new_problem to a problem already in the history: {sum(v['repeat'] for v in rows.values())}")
        print(f"- deterministic on a second call: {all(v['deterministic'] for v in rows.values())}")


if __name__ == "__main__":
    for config in sys.argv[1:]:
        version, eligibility = config.split(":")
        res = run(version, eligibility)
        (OUT / f"recommendations-{version}-{eligibility}.json").write_text(json.dumps(res, indent=0, sort_keys=True))
        summary(f"policy {version}, eligibility {eligibility}", res, {"e2": E2, "current": CURRENT}[eligibility])
        trajectories(version, eligibility)
