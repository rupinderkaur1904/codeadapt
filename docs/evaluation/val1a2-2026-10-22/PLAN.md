# VAL1-A2 analysis plan: mutation audit of the three remaining problems

**Status.** This plan is frozen. It was committed, together with the correct originals and
the behaviour driver, before any mutant was generated or run. The owner authorised it on
2026-10-22 as a bounded, synthetic validation task, following the ADR-027 milestone.
Anything decided after this commit is reported as a deviation.

**Question.** Does the failure pattern found in VAL1-A on lower-bound generalise to
`count-occurrences`, `last-less-than` and `first-true`, now that the production method is
v1.2? The pattern had three parts:

- low coverage;
- wrong names concentrated in one class of coarse evidence;
- dependence on the reference's coding style.

The audit asks four things of single-edit mutants of three correct styles per problem:

1. How often does the method name an error model?
2. When it names one, is the mutant's behaviour actually that model's behaviour?
3. Do coarse signatures (runtime crash, memory limit) drive wrong names, as time limits
   did before ADR-027?
4. How much does coverage depend on the style the error models were written in?

**What this is not.** The mutants are synthetic and mechanically generated, and an AI
system working on this project wrote the plan. The results are:

- not independent validation;
- not real-student evidence;
- not evidence about learning;
- not a basis for resuming CE1.2 or CE1.3 or expanding the problem bank, whatever they
  show.

## 1. Frozen inputs

**Method.** `fingerprint_consistency` 1.2 (`METHODS["v1"]`), the production method since
ADR-027. Each diagnosis is also recomputed with `METHODS["v1.1"]` on the same evidence,
but only as a secondary comparison.

**Content.** These are used unchanged. Fingerprints are measured fresh by the same code
the evaluation harness uses.

| Problem | Content version | Tests | Error models |
| --- | --- | --- | --- |
| count-occurrences | `d1b043c04574` | 15 | 4 |
| last-less-than | `3d52811ae14b` | 15 | 5 |
| first-true | `b69c5efa3b39` | 19 | 9 |

The audit stops (§9, X2) if a content version differs or content validation fails.

**Pipeline.** Each mutant goes through `collect_evidence` and the method, as
`evaluation/runner.py::_case` does:

- standard build, sanitizer build, repeat runs of failing tests, infrastructure
  re-measurement;
- **2 runs per mutant**.

The audit runner records every observation, with its exclusion reason, for both runs. It
changes no production code.

**Environment.** g++ 14.2.0 under runc, image `codeadapt-sandbox:gcc14.2-1`.

**Not changed:**

- production code, content, skill maps, ledger, BKT and recommendation policy;
- every existing evaluation result, including VAL1-A and the ADR-027 re-run.

## 2. Correct implementation styles (originals)

The originals are in `eval/mutation/<problem>/originals/`.

| Style | File | Structure |
| --- | --- | --- |
| A | `half_open.cpp` | A verbatim copy of the problem's `reference.cpp`. **The error models were derived from this style**, so it is the expected best case. |
| B | `closed_answer.cpp` | Closed `[lo, hi]` with `hi = n - 1` and an answer variable. |
| C | `recursive.cpp` | A recursive helper over a half-open `[lo, hi)`. |

For count-occurrences, every style puts the search in one helper, called twice
(`> target` and `>= target` boundaries) and subtracted.

All 9 originals were checked before this commit: each matches its reference on every
input of the behaviour set (§5). Each must also give `no_failure_observed` in the pipeline.
If one does not, the audit stops (§9, X1).

## 3. Mutation operators and inclusion

The operators, inclusion and exclusion rules are the same as VAL1-A PLAN.md §3:

- ROR, AOR, ICR, UOI, DEL, NEG, SDL;
- one edit per mutant, inside function bodies only;
- signatures, `#include` lines and comments are never mutated;
- duplicates and no-op edits are listed, not run.

Two adaptations, both mechanical:

- the size expression `static_cast<int>(flags.size())` is treated like
  `static_cast<int>(a.size())`;
- UOI also applies to reads of `n` (count-occurrences, style C).

**Every** kept mutant is run. There is no sampling.

## 4. Labels: behavioural, objective, computed before any pipeline run

VAL1-A used concept labels hand-assigned by the plan author. VAL1-A2 uses a **behavioural
label** instead, which needs no judgement. It is computed natively (§5) before the
pipeline runs:

- `reference`: the mutant matches the reference on every input of the behaviour set.
- `model:<key>`: the mutant matches error model `<key>`'s program on every input. TLE and
  CRASH count as values, so a stalling mutant matches a stalling model only if it stalls
  on the same inputs and agrees on all the others. If several models match, all are
  listed (`models`).
- `none`: the mutant matches neither the reference nor any model.

For a mutant labelled `none`, the label is the edit, not a library error. A diagnosis
naming any model for it is a **behavioural mismatch**: the named model does not describe
what the program does. This holds even if the edit is "in the spirit" of the model's
description.

**Comparability with VAL1-A.** The same behavioural labels are computed for the 147
lower-bound mutants of VAL1-A, natively only, with nothing re-executed in the sandbox.
They are scored against the recorded VAL1-A evidence as replayed under v1.2
(`../adr027-2026-10-21/val1a.json`). That gives a four-problem picture with one label
definition. VAL1-A's concept labels are not changed.

**Limitation stated in advance.** Behavioural labels judge the program, not the
misconception. A mutant whose edit differs from a model's but behaves identically
everywhere counts as matching that model. A mutant that has the model's error plus a
harmless-looking change that alters behaviour off-suite counts as `none`.

## 5. Behaviour set and equivalence

The behaviour set is fixed by `behaviour_driver.cpp` (compiled `g++ -O1 -std=c++17`):

- **Sorted-array problems:** 3000 sorted arrays, `n` from 0 to 20, values 0–9, targets
  −1 to 10, seed 20261021; plus 20 arrays each of `n` = 1000 and 4096, values 0–59.
- **first-true:** the same sizes. Each array is a block of 0s followed by a block of 1s,
  with the number of 1s drawn uniformly from 0 to `n`.
- **Execution:** each input runs in a forked child with a 50 ms CPU limit, giving TLE.
  A crash gives CRASH.

"Equivalent" and "matches" mean equal on the tested inputs, never proven.

## 6. Classification (as VAL1-A §6)

1. **`compile_error`.**
2. **`unreliable`:** `execution_error`, `unreliable_evidence`, or not reproducible across
   the 2 runs (outcome, model or any signature differs).
3. **`passes_suite`:** `no_failure_observed`, split into:
   - `equivalent` (behavioural label `reference`);
   - `suite_gap` (any other label).
4. **`incorrect_failing`:** reliably evaluated with at least one failing test. Split by
   v1.2 outcome:
   - `hypothesis_supported`, unqualified or qualified;
   - `non_termination_observed`;
   - `ambiguous`;
   - `insufficient_evidence`;
   - `unmodelled_behaviour`.

## 7. Metrics

Every metric is reported per problem, per style, and pooled over the three problems, as
count over denominator with a Wilson 95% interval. The four-problem pool, adding replayed
lower-bound, is reported separately.

- **Named coverage:** `hypothesis_supported` / `incorrect_failing`.
- **Symptom rate:** `non_termination_observed` / `incorrect_failing`.
- **Behavioural precision:** named diagnoses whose model is among the mutant's matching
  models / named diagnoses. **Wrong name** is the complement. It is reported:
  - for unqualified and qualified diagnoses separately;
  - with each wrong name listed;
  - with **cross-skill** cases flagged, meaning the label is `none` or a model of a
    different skill.
- **Library recall:** mutants labelled `model:M` that are `incorrect_failing` and
  diagnosed as M / mutants labelled `model:M` that are `incorrect_failing`.
- **Collisions:** for each named model, the number of distinct mutants and distinct labels
  diagnosed as it, and groups of mutants with identical full signature vectors but
  different labels.
- **Suite gap:** `suite_gap` / reliable, compiling, non-equivalent mutants.
- **Style dependence:** named coverage in style A against pooled styles B and C.

**Coarse-signature checks (ADR-027 Q3):**

- the number of mutants with any reliable `runtime_error` or `memory_limit` observation;
- the number with any excluded observation, by reason (sanitizer kind, non-determinism,
  inconclusive);
- for named diagnoses, the share whose supporting tests are **only** `runtime_error` or
  `memory_limit` signatures, and their wrong-name rate;
- native CRASH or TLE behaviour against the pipeline's signatures, as a cross-check.

**Secondary:** the same coverage and precision under v1.1 on the same evidence. This
shows how much ADR-027 changed on these problems.

## 8. Decision readings (pre-registered)

| ID | Condition (pooled over the three problems, v1.2) | Reading |
| --- | --- | --- |
| G1 | Wrong-name rate ≥ 10%, or its Wilson upper bound ≥ 20% | Precision concern generalises beyond time limits; the naming rules need redesign before human data. |
| G1b | Any **unqualified** cross-skill wrong name | Listed individually. Each would have become an `incorrect` skill observation. |
| G2 | Named coverage < 20% | Low coverage generalises. The library covers few single-edit errors on all four problems. |
| G3 | Pooled B+C named coverage < half of style A | Style dependence generalises. |
| G4 | Suite gap > 10% | The suites miss incorrect programs; diagnoses depend on incomplete suites. |
| G5 | Any wrong name whose supporting evidence is only `runtime_error` or `memory_limit` signatures | Coarse-signature concern (Q3) confirmed. Those signatures need the ADR-027 treatment. |
| G0 | Fewer than 10 named diagnoses pooled | Precision is **not evaluable**. That is reported as such, never as a pass. |

Each reading is also given per problem, as description, with no decision rule.

These readings inform the memo. **None of them, alone or together, authorises a
production change, content change, CE1.2/CE1.3, or problem-bank expansion.**

## 9. Stop conditions

The audit stops and reports, without working around the problem, if:

| ID | Condition |
| --- | --- |
| X1 | An original does not give `no_failure_observed` in the pipeline. Only the original may be fixed, recorded as a deviation; content is never changed. |
| X2 | A content version differs from §1, or content validation fails. |
| X3 | More than 10% of a problem's mutants end in `execution_error` after re-measurement. This is an environment problem, so it is reported instead of results. |
| X4 | The v1.1 recomputation of any lower-bound record in `../val1a-2026-10-21/` fails to reproduce. This would mean the evidence code changed. |
| X5 | The projected sandbox run time exceeds 24 hours. Report the mutant count and ask before continuing; do not sample. |

Whatever the results, the audit **stops at the VAL1-A2 gate**. It ends with the results and
a decision memo:

- whether the pattern generalises;
- what the evidence supports;
- what remains unknown.

## 10. Reproducibility

The following are committed:

- the originals, behaviour driver, generator, label script, audit runner and analysis
  script;
- every mutant and the manifests;
- the behavioural labels;
- the raw per-run records (every observation and exclusion);
- the report.

Running the generator and labeller again from a clean checkout must reproduce identical
mutants and labels. The analysis must reproduce the report from the raw records. A
`MANIFEST.sha256` of the inputs and results is committed with the results.
