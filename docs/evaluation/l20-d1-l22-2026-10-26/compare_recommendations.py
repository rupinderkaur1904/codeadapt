"""Compare two recommendation_regression.py outputs (before.json after.json)."""

import json
import sys

before, after = (json.load(open(p)) for p in sys.argv[1:3])
assert set(before) == set(after), set(before) ^ set(after)
choice = [k for k in before if any(before[k][f] != after[k][f] for f in ("rule", "action", "problem", "flag"))]
names = [k for k in before if k not in choice and before[k] != after[k]]
print(f"cases: {len(before)}")
print(f"rule, action, problem or review flag differs: {len(choice)}")
for k in choice:
    print("  ", k, before[k], after[k])
print(f"only target or criterion skill names differ: {len(names)}")
for k in names:
    print(f"   {k}: {before[k]['skills']} -> {after[k]['skills']}")
