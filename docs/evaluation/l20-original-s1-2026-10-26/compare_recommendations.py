"""Compare two recommendation_regression.py outputs (before.json after.json)."""

import json
import sys

before, after = (json.load(open(p)) for p in sys.argv[1:3])
assert set(before) == set(after), set(before) ^ set(after)
fields = ("rule", "action", "problem", "skills", "flag", "crit")
choice = [k for k in before if any(before[k][f] != after[k][f] for f in fields)]
qualified = [k for k in before if before[k]["qualified"] != after[k]["qualified"]]
print(f"cases: {len(before)}")
print(f"rule, action, problem, target skills, review flag or criterion differs: {len(choice)}")
for k in choice:
    print("  ", k, before[k], after[k])
print(f"qualified_hypothesis differs: {len(qualified)}")
for k in qualified:
    print(f"   {k}: {before[k]['qualified']} -> {after[k]['qualified']}")
