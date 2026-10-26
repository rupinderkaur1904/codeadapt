"""Preview only: rank follow-ups by share of tests probing the skill (P1), and also skip problems where the skill is positive-only (P2)."""
import collections, sys
sys.argv=["x"]
import analyse as A
from codeadapt.adaptation import policy_v1 as pv
from codeadapt.adaptation.ledger import tests_probing
EFF=A.EFF
def make(skip_pos):
    def dens(family, skills, recent, fallback):
        rows=[]
        for p in family:
            n=len(tests_probing(p, skills))
            if n==0: continue
            if skip_pos and any(s in p.positive_only_skills or (p.slug,s) in EFF for s in skills): continue
            rows.append((p, n/len(p.tests)))
        rows.sort(key=lambda r:(r[0].slug in recent, -r[1], r[0].slug))
        return (rows[0][0] if rows else fallback), []
    return dens
for label, sp in (("P1 share", False), ("P1+P2 share, skip positive-only", True)):
    pv.PolicyV1._densest = staticmethod(make(sp))
    res = A.run(A.ALL)
    print(label, dict(collections.Counter(v[1] for v in res.values() if v[0]=="new_problem").most_common(12)))
    for k in ("lower-bound|named:stops_at_first_match","last-less-than|named:uses_le","lower-bound|named:upper_bound_confusion"):
        print("   ", k, "->", res[k][:2])
