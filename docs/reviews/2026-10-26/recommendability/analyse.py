"""Per-problem follow-up capacity and a preview of policy 1.4 choices with every problem recommendable."""
import collections, itertools, json, sys
from codeadapt.diagnosis import Outcome
from codeadapt.adaptation.policy_v1 import PolicyV1
from tests.unit.test_adaptation import PROBLEMS, attempt

P = PolicyV1()
ALL = {s: p.model_copy(update={"recommendable": True}) for s, p in PROBLEMS.items()}

print("== capacity")
for slug, p in sorted(PROBLEMS.items(), key=lambda kv: (kv[1].family, kv[0])):
    probes = collections.Counter(s for t in p.tests for s in p.skills_probed_by(t))
    models = collections.Counter(m.skill for m in p.error_models)
    lim = sorted(m.key for m in p.error_models if m.known_limitation)
    print(f"{p.family:14} {slug:20} rec={p.recommendable!s:5} tests={len(p.tests)} probes={dict(sorted(probes.items()))} models={dict(sorted(models.items()))} pos_only={sorted(p.positive_only_skills)} lim={lim}")

def run(problems):
    out = {}
    for slug, spec in sorted(problems.items()):
        first = spec.tests[0].key
        cases = [("nofail", attempt(slug, Outcome.NO_FAILURE_OBSERVED))]
        for m in spec.error_models:
            fail = tuple(t.key for t in spec.tests if m.key in (t.distinguishes or ())) or (first,)
            cases.append((f"named:{m.key}", attempt(slug, Outcome.HYPOTHESIS_SUPPORTED, model=m.key, failing=fail)))
        for a, b in itertools.combinations([m.key for m in spec.error_models], 2):
            cases.append((f"amb:{a}+{b}", attempt(slug, Outcome.AMBIGUOUS, candidates=(a, b), failing=(first,))))
        for name, a in cases:
            r = P.recommend(a, [a], problems)
            out[f"{slug}|{name}"] = (str(r.action), r.problem_slug, tuple(r.target_skills))
    return out

before, after = run(PROBLEMS), run(ALL)
changed = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
print("\n== preview: cases", len(before), "changed", len(changed))
dest_b = collections.Counter(v[1] for v in before.values() if v[0] == "new_problem")
dest_a = collections.Counter(v[1] for v in after.values() if v[0] == "new_problem")
act_b = collections.Counter(v[0] for v in before.values()); act_a = collections.Counter(v[0] for v in after.values())
print("actions before", dict(act_b)); print("actions after ", dict(act_a))
print("new_problem destinations before", dict(dest_b.most_common()))
print("new_problem destinations after ", dict(dest_a.most_common()))
for k in sorted(changed)[:400]:
    if k.split("|")[1] in ("nofail",) or k.startswith(("lower-bound|named", "last-less-than|named", "count-occurrences|named")):
        print(" ", k, changed[k][0], "->", changed[k][1])

EFF = {("count-occurrences","equality_handling"),("count-occurrences","loop_termination"),("last-less-than","loop_termination"),("last-occurrence","loop_termination"),("min-capacity","loop_termination"),("rotated-min","loop_termination"),("lower-bound","loop_termination"),("upper-bound","loop_termination")}
def posonly(res, problems):
    n=tot=0; ex=collections.Counter()
    for k,(act,dest,skills) in res.items():
        if act!="new_problem" or "nofail" in k: continue
        tot+=1
        for sk in skills:
            if sk in problems[dest].positive_only_skills or (dest,sk) in EFF:
                n+=1; ex[(dest,sk)]+=1; break
    return n,tot,ex
for name,res,pr in (("before",before,PROBLEMS),("after",after,ALL)):
    n,tot,ex=posonly(res,pr)
    print(f"{name}: targeted follow-ups {tot}, to a problem where a target skill is positive-only {n}", dict(ex.most_common(8)))

print("\n== subsets")
NONBS = {s for s,p in PROBLEMS.items() if p.family != "binary-search"}
for label, extra in (
    ("C1: siblings upper-bound,last-occurrence,exact-search,first-true + non-binary", {"upper-bound","last-occurrence","exact-search","first-true"} | NONBS),
    ("C2: C1 + integer-sqrt,min-capacity,peak-index", {"upper-bound","last-occurrence","exact-search","first-true","integer-sqrt","min-capacity","peak-index"} | NONBS),
):
    sub = {s: (p.model_copy(update={"recommendable": True}) if s in extra else p) for s,p in PROBLEMS.items()}
    res = run(sub)
    ch = sum(1 for k in before if before[k] != res[k])
    print(label, "changed", ch, "dest", dict(collections.Counter(v[1] for v in res.values() if v[0]=="new_problem").most_common()))
    for k in ("lower-bound|named:stops_at_first_match","last-less-than|named:uses_le","count-occurrences|nofail","lower-bound|nofail"):
        print("   ", k, before[k][:2], "->", res[k][:2])
