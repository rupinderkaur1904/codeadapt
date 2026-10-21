# VAL1-A analysis plan: lower-bound mutation audit

**Status.** This plan was committed before any mutant was generated or run. It was
approved in scope by the owner on 2026-10-21, as VAL1 stage A, following
`critical-review.md` §3.6. Anything decided after this commit is marked as a deviation in
the results.

**Question.** On single-edit mutants of three independently structured, correct
lower-bound implementations, how does the production diagnostic method behave?
- How often does it name an error model?
- How often is the named model a different error from the edit that was made?
- Which models collect many different edits?
- How much of this depends on the implementation style the error models were derived
  from?

**What this is not.** Mutants are synthetic, mechanically generated, and labelled by the
same AI system that works on this project. This is not independent validation, not
real-student evidence, and not evidence about learning. A high coverage number does not
by itself justify resuming CE1.2 or CE1.3.

## 1. Frozen inputs

- **Method:** `fingerprint_consistency` v1.1 (`METHODS["v1"]`), the production method.
  `v2-candidate` is not used.
- **Content:** `content/demo/lower-bound`, version `871602bc2bba`, unchanged.
  - Its 17 tests and 8 error models are used as they are.
  - Fingerprints are measured fresh in this environment, by the same code the evaluation
    harness uses.
- **Pipeline:** each mutant goes through `evidence.collect.collect_evidence` and
  `FingerprintConsistencyV1.diagnose`, exactly as `evaluation/runner.py::_case` does.
  - This covers the standard build, the sanitizer build, repeat runs of failing tests,
    and infrastructure re-measurement.
  - **2 runs per mutant**, as in earlier evaluations.
  - The audit script records extra fields: excluded tests and their reasons,
    `support_behaviours`, and the qualification. It changes no production code.
- **Environment:** g++ 14.2.0 under runc, image `codeadapt-sandbox:gcc14.2-1`.
- **Not changed:** production code, content, skill maps, BKT, recommendation policy, and
  the existing held-out and calibration sets and results.

## 2. Correct implementation styles (originals)

These are in `eval/mutation/lower-bound/originals/`.

| Style | File | Structure |
| --- | --- | --- |
| A | `half_open.cpp` | A verbatim copy of the content's reference: half-open `[lo, hi)`, `lo = mid + 1` / `hi = mid`, `return lo`. **The error models were derived from this style**, so it is the expected best case for the library. |
| B | `closed_answer.cpp` | Closed `[lo, hi]`, `hi = n - 1`, answer variable `ans = n`, test `a[mid] >= target`, `return ans`. |
| C | `recursive.cpp` | Recursive helper over half-open `[lo, hi)`, base case `lo >= hi`, wrapper call `search(a, target, 0, n)`. |

Before mutation, each original must pass all 17 tests (NO_FAILURE_OBSERVED) and match the
reference on the random-input set in §5. If one fails, it is fixed and the fix is
recorded as a deviation.

## 3. Mutation operators

Edits are made at the token level, inside function bodies only. Signature lines,
`#include` lines and comments are never mutated. Each mutant contains exactly one edit.

| ID | Operator | Rule |
| --- | --- | --- |
| ROR | Relational operator replacement | Each `<`, `<=`, `>`, `>=`, `==`, `!=` is replaced by each of the other five. Template brackets are excluded. |
| AOR | Additive operator replacement | Each binary `+` becomes `-`, and each binary `-` becomes `+`. |
| ICR | Integer constant replacement | Each integer literal `k` becomes `k + 1` and `k - 1`. |
| UOI | Operand off-by-one insertion | Each *read* of `lo`, `hi`, `mid` or `ans`, and each `static_cast<int>(a.size())`, becomes `(x + 1)` and `(x - 1)`. A read is any occurrence that is not the target of an assignment or declaration. Array indices are included. |
| DEL | Off-by-one removal | Each `+ 1` / `- 1` term is deleted (for example `mid + 1` becomes `mid`). |
| NEG | Condition negation | Each `if` / `while` condition `c` becomes `!(c)`. |
| SDL | Statement deletion | Each assignment statement that is not a declaration is deleted. |

**Inclusion.** Every mutant the operators produce.

**Exclusion.** These are counted and listed, never silently dropped:
- a mutant whose source text is identical to an earlier mutant: keep the first, record
  the duplicate;
- a mutant identical to its original.

## 4. A-priori concept labels (before any run)

After generation and **before the pipeline runs**, a rule-based labeller (`label.py`,
committed with the mutants) gives each mutant one *concept label*. The label is either:
- the lower-bound error model whose described error the edit expresses; or
- `none`, when the edit expresses no modelled error.

| Concept label | The edit is labelled with it when it… |
| --- | --- |
| `upper_bound_confusion` | sends equal elements right: `a[mid] < target` → `<=` (styles A, C), `a[mid] >= target` → `>` (B) |
| `hi_init_last_index` | starts a half-open search at `n - 1`: UOI `-1` on the initial `static_cast<int>(a.size())` (A, C) |
| `no_progress_update` | makes the left update `lo = mid` in a half-open search: DEL on `mid + 1` (A, C) |
| `hi_skips_candidate` | makes the right update `hi = mid - 1` in a half-open search: UOI `-1` on `mid` in the `hi` update (A) or in the right recursive call (C) |
| `closed_loop_hi_mid` | makes a half-open loop closed while keeping `hi = mid`: `lo < hi` → `lo <= hi` (A); base case `lo >= hi` → `lo > hi` (C) |
| `returns_wrong_pointer` | returns the index one before the boundary: UOI `-1` on the returned value (`return lo`, `return ans`, or base case `return lo`) |
| `exact_match_sentinel`, `stops_at_first_match` | not reachable by a single edit here; expected count 0 |
| `none` | every other mutant |

These labels are the plan author's judgement, written before any result. They are
**not human labels**. Mutants where the label is debatable are listed for owner review.

## 5. Ground truth on behaviour (separate from concept labels)

Each mutant is also run natively (`g++ -O1`), outside the product sandbox, as analysis
only. It is compared with the reference on a fixed random-input set:
- 3000 sorted arrays, `n` from 0 to 20, values 0–9, targets −1 to 10, seed 20261021;
- plus `n` = 1000 and 4096 arrays.

Each input runs in a forked child with a 50 ms CPU limit.

- **Equivalent:** identical to the reference on every input. Called "equivalent on the
  tested inputs", never proven equivalent.
- **Non-equivalent:** differs on at least one input.

## 6. Classification of every mutant

These categories are mutually exclusive and are always reported separately:

1. `compile_error` (pipeline).
2. `unreliable`: `execution_error` or `unreliable_evidence` (pipeline), or not
   reproducible across the 2 runs.
3. `passes_suite`: `no_failure_observed`, split by §5 into:
   - `equivalent`;
   - `suite_gap`: incorrect but passes all 17 tests.
4. `incorrect_failing`: reliably evaluated with at least one failing test. Split by
   outcome:
   - `hypothesis_supported`, unqualified or qualified;
   - `ambiguous`;
   - `insufficient_evidence`;
   - `unmodelled_behaviour`.

## 7. Metrics

Every metric is reported per style and pooled, as a count over a stated denominator, with
a Wilson 95% interval.

- **Coverage** = diagnosed / `incorrect_failing`. Diagnosed means `hypothesis_supported`,
  qualified or not.
- **Abstention by outcome** = each abstaining outcome / `incorrect_failing`.
- **Concept agreement** = diagnoses whose model equals the concept label / diagnoses.
- **Cross-pattern diagnoses** = diagnoses whose model differs from the concept label,
  including label `none` / diagnoses. These are reported:
  - with each case listed;
  - unqualified and qualified separately;
  - with **cross-skill** cases flagged. These are cases where the diagnosed model's skill
    differs from the label's skill, or the label is `none`.
- **Library recall on labelled mutants** = labelled mutants (label ≠ `none`) diagnosed
  with their label / labelled mutants that are `incorrect_failing`.
- **Collisions** = for each model, the number of distinct mutants and distinct concept
  labels diagnosed as it, and the sets of mutants with identical full signature vectors.
- **Suite gap** = `suite_gap` / non-equivalent compiling, reliable mutants.
- **Generator bias**:
  - the share of mutants with a library concept label, per style;
  - the operators that can and cannot express each model;
  - coverage in style A against styles B and C.

## 8. Decision thresholds (pre-registered)

| ID | Condition | Reading |
| --- | --- | --- |
| T1 | Cross-pattern diagnoses ≥ 10% of diagnoses, or the Wilson upper bound ≥ 20% | Precision concern even on single edits. Redesign of the support or qualification rules goes ahead of VAL1-B. |
| T1b | Any **unqualified** cross-skill diagnosis | Listed individually. Each one would have become an `incorrect` skill observation. |
| T2 | Coverage < 20% | The library covers few single-edit errors. Expect lower coverage on human-written code. |
| T3 | Pooled B+C coverage < half of style A coverage | The library is bound to the reference's convention. A style-dependent model library is a design limitation to resolve. |
| T4 | Suite gap > 10% of non-equivalent reliable mutants | The suite misses incorrect programs. Diagnoses are conditional on an incomplete suite. |

None of these outcomes, alone or together, resumes CE1.2 or CE1.3. The results go to the
owner at the VAL1-A gate, and the VAL1-B protocol is proposed separately for approval.

## 9. Reproducibility

The following are committed:
- the generator, labeller, audit runner, equivalence checker and analysis script;
- every mutant source and the manifest;
- raw per-mutant results (JSON) and the report.

Running the scripts again from a clean checkout must reproduce the same mutants, labels
and classifications in the same environment.
