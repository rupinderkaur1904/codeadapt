"""Policy 1.4 recommendations for one-attempt synthetic histories, as JSON (ADR-037 check).

Run from backend/ with PYTHONPATH=. in two checkouts, before and after the change, then
compare with compare_recommendations.py. For every problem: a no-failure attempt, an
unmodelled attempt, each error model named (failing the tests it is measured to fail), and
each pair of models ambiguous. Synthetic inputs only; this checks that the policy's choices
are unchanged, nothing about accuracy.
"""

import itertools
import json

from codeadapt.diagnosis import Outcome
from tests.unit.test_adaptation import POLICY, PROBLEMS, attempt

out = {}
for slug, spec in sorted(PROBLEMS.items()):
    first = spec.tests[0].key
    cases = [
        ("nofail", attempt(slug, Outcome.NO_FAILURE_OBSERVED)),
        ("unmodelled", attempt(slug, Outcome.UNMODELLED_BEHAVIOUR, failing=(first,))),
    ]
    for m in spec.error_models:
        fail = tuple(t.key for t in spec.tests if m.key in (t.distinguishes or ())) or (first,)
        cases.append(
            (f"named:{m.key}", attempt(slug, Outcome.HYPOTHESIS_SUPPORTED, model=m.key, failing=fail))
        )
    for a, b in itertools.combinations([m.key for m in spec.error_models], 2):
        cases.append(
            (f"amb:{a}+{b}", attempt(slug, Outcome.AMBIGUOUS, candidates=(a, b), failing=(first,)))
        )
    for name, a in cases:
        r = POLICY.recommend(a, [a], PROBLEMS)
        out[f"{slug}|{name}"] = {
            "rule": str(r.rule),
            "action": str(r.action),
            "problem": r.problem_slug,
            "skills": list(r.target_skills),
            "flag": r.review_flag,
            "crit": None if r.criterion is None else list(r.criterion.skills),
            "qualified": r.rationale.get("qualified_hypothesis"),
        }
print(json.dumps(out, sort_keys=True, indent=0))
