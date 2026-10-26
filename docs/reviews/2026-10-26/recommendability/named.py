import collections, sys
sys.argv=["x"]
import analyse as A
NONBS={s for s,p in A.PROBLEMS.items() if p.family!="binary-search"}
C1={"upper-bound","last-occurrence","exact-search","first-true"}|NONBS
sub={s:(p.model_copy(update={"recommendable":True}) if s in C1 else p) for s,p in A.PROBLEMS.items()}
for label,pr in (("current",A.PROBLEMS),("all 25",A.ALL),("C1",sub)):
    res=A.run(pr)
    for kind in ("named:","amb:","nofail"):
        c=collections.Counter((v[1] if v[0]=="new_problem" else v[0]) for k,v in res.items() if kind in k and A.PROBLEMS[k.split("|")[0]].family=="binary-search")
        print(f"{label:8} {kind:7} n={sum(c.values())}", dict(c.most_common(8)))
