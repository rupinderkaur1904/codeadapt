"""L19 focused analysis: per-outcome breakdown of the 421 synthetic incorrect programs.

Reads committed records only (nothing is re-executed):
- docs/evaluation/adr030-replay-2026-10-22/cases.json: the `candidate` runs equal production
  v1.3 on all 1,366 runs (docs/evaluation/adr030-2026-10-23) and carry the skill observations
  the production pipeline computed under the current evidence rules (rule C included);
- the `truth` field there: the VAL1-A/A2 behavioural label, computed natively by a script
  (`model:<key>` when the mutant is output-identical to that error model on the label
  inputs, otherwise `none`). It is not an independent, human or skill-level label.
- problem.toml of the four problems, for each model's skill.

Run from the repository root: python3 docs/reviews/2026-10-25/l19_breakdown.py
"""

import collections
import json
import tomllib

cases = json.load(open("docs/evaluation/adr030-replay-2026-10-22/cases.json"))
model_skill = {}
for slug in ("lower-bound", "count-occurrences", "last-less-than", "first-true"):
    spec = tomllib.load(open(f"content/demo/{slug}/problem.toml", "rb"))
    for m in spec["error_models"]:
        model_skill[(slug, m["key"])] = m["skill"]

table = collections.Counter()
per_outcome_obs = collections.Counter()
correct_counts = collections.Counter()
label_check = collections.Counter()
programs = 0
for case in cases:
    if case["set"] not in ("val1a", "val1a2") or case["category"] != "incorrect_failing":
        continue
    programs += 1
    run = case["runs"]["candidate"][0]
    named = (
        run["outcome"] == "hypothesis_supported"
        and run["evidence_strength"] != "single_behaviour"
        and not run["known_limitation"]
    )
    outcome = run["outcome"]
    if outcome == "hypothesis_supported":
        outcome = "named, unqualified" if named else "named, qualified"
    obs = run["skill_observations"]
    correct = [o.split(":")[0] for o in obs if o.endswith(":correct")]
    incorrect = [o.split(":")[0] for o in obs if o.endswith(":incorrect")]
    shape = (
        "no observation" if not obs
        else "incorrect only" if not correct
        else "correct only" if not incorrect
        else "incorrect + correct"
    )
    table[(outcome, shape)] += 1
    per_outcome_obs[(outcome, "correct")] += len(correct)
    per_outcome_obs[(outcome, "incorrect")] += len(incorrect)
    correct_counts[len(correct)] += 1

    truth = case.get("truth") or "none"
    if truth.startswith("model:"):
        skill = model_skill[(case["problem"], truth.split(":", 1)[1])]
        label_check["labelled with a model"] += 1
        if correct:
            label_check["labelled, with >=1 correct obs"] += 1
        if skill in correct:
            label_check["correct obs ON the labelled model's skill"] += 1
        if skill in incorrect:
            label_check["incorrect obs on the labelled model's skill"] += 1
    else:
        label_check["label none (no skill label exists)"] += 1
        if correct:
            label_check["label none, with >=1 correct obs"] += 1

print("incorrect programs:", programs)
print("\noutcome x observation shape (programs)")
for (outcome, shape), n in sorted(table.items()):
    print(f"  {outcome:28} {shape:22} {n}")
print("\nobservations per outcome")
for (outcome, value), n in sorted(per_outcome_obs.items()):
    print(f"  {outcome:28} {value:10} {n}")
print("\nprograms by number of correct observations:", dict(sorted(correct_counts.items())))
print("\nbehavioural-label check:")
for k, n in label_check.items():
    print(f"  {k}: {n}")
