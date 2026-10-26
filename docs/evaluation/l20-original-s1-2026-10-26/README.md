# Re-run after L20 S1 for the original problems (ADR-037, 2026-10-26)

**Why.** ADR-037 added a `known_limitation` to four models:

- lower-bound `upper_bound_confusion` (O1);
- last-less-than `uses_le` (O2) and `clamps_to_zero` (O3);
- first-true `none_sentinel` (O4).

last-less-than also gained a `positive_only_skills` reason. Those three problems therefore
have new content versions.

The diagnosis method does not read `known_limitation`, so diagnoses were expected to be
unchanged. This record checks that. **All earlier evaluation records are preserved
unchanged.**

**Environment.** g++ 14.2.0, `runc`, image `codeadapt-sandbox:gcc14.2-1`, 2 runs per case.

## Content versions

| Problem | Before (f752a51) | After |
| --- | --- | --- |
| lower-bound | `9aade9e1396e` | `8ca53699ef0d` |
| last-less-than | `4208517a8d24` | `ecdcad684935` |
| first-true | `485c974b4928` | `c5285489e34a` |

The other 22 problems are unchanged.

## 1. Held-out cases: diagnoses unchanged

**Command** (from `backend/`, for `<p>` in lower-bound, last-less-than and first-true):

```
uv run codeadapt-eval --content ../content/demo --heldout ../eval/heldout --problem <p> \
  --runs 2 --compare v1.1 v1.2 v1 --json ../docs/evaluation/l20-original-s1-2026-10-26/heldout/<p>.json \
  --markdown ../docs/evaluation/l20-original-s1-2026-10-26/heldout/<p>.md
```

**Comparison.** `python3 docs/evaluation/l20-original-s1-2026-10-26/compare_heldout.py`
compares against `../l20-d1-l22-2026-10-26/heldout/`; output in `heldout_comparison.txt`.
It covers 78 case × method results: 26 cases under v1.1, v1.2 and v1.3.

**Result:** 78 identical, 0 changed. Outcome, named model, candidates, classification and
reproducibility are all identical.

**Synthetic, author-written cases.** This is not an accuracy estimate for real students.

## 2. Content reports: measurements unchanged

`codeadapt-content report content/demo/<p> --out docs/content-reports` was run for the three
problems (log: `content-report.log`); each gives `RESULT ok`.

The reports change in exactly two ways:

- the content version line;
- the "Documented limitation" cell of the four models.

The matrices, detecting-test counts, behaviour groups, pairs and validation results are
unchanged (`git diff` of docs/content-reports/).

## 3. Recommendations: choices unchanged

`recommendation_regression.py` was run at f752a51 (a worktree, `PYTHONPATH` set to it) and at
this change. It covers 442 one-attempt synthetic histories, every problem with: no failure,
unmodelled, every model named, and every model pair ambiguous.

`compare_recommendations.py` compares them (`recommendation_comparison.txt`):

- **Rule, action, chosen problem, target skills, review flag and criterion:** identical in
  all 442 cases.
- **`qualified_hypothesis`:** differs in exactly 4 cases, the four models named, from false
  to true. That is the intended ADR-037 change.

## 4. Banned names in stored evaluation programs, after the detector fix

The 2026-10-26 D1 audit fixed a false positive: a student's own lambda or function object
named like a banned call was counted as the library call.

`../l20-d1-l22-2026-10-26/banned_name_replay.py ..`, run from `backend/`
(`banned_name_replay.txt`), covers 845 programs. 0 name a banned call of their problem, as
before.

## 5. Effective positive-only skills

`effective_positive_only.py` (`effective_positive_only.txt`) lists, for every problem, the
skills that no model can give negative evidence for. It uses the measured fingerprints and
diagnosis v1.3 rules 4b, 7, single behaviour and 8a, as well as `known_limitation`.

- 12 skills are declared positive-only.
- 8 more are positive-only only through those rules, and are not declared. These are mostly
  `loop_termination`, whose models time out.

The bank status matrix (docs/reviews/2026-10-26/bank-status/) discusses them.

## 6. Scripted demo

`python3 docs/demo/run_demo.py` was run against a fresh dev API and worker, using SQLite and
runc. The output is in `demo_run.txt`. It took 2 min 29 s.

- **Outcomes:** identical to docs/demo.md for all four programs.
- **Changed:** `upper_bound_closed.cpp` now gets the qualified student message, with the same
  hint.
- **Final recommendation:** unchanged.

## Not covered

- **Real-student accuracy and calibrated mastery:** none claimed. The BKT parameters
  (`bkt-params-assumed-1`) and policy 1.4 are unchanged.
- **Attempts in dev and test databases:** keep their versions' snapshots. Only those
  databases hold attempts.
