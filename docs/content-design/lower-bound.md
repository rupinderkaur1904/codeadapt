# Content design, worked example: `lower-bound`

> **Update 2026-10-26.** New content version `9aade9e1396e…` (was `871602bc2bba…`). The record below describes the problem as designed and is unchanged.
>
> **Banned names (ADR-035).** `banned_names` lists `std::equal_range`, `std::lower_bound`, `std::partition_point`, `std::upper_bound`; an attempt that names one gives no skill observations.

This document applies the content-design method in [README.md](README.md) to one problem,
starting from what is actually in the repository. It covers two things:

* **As built.** These numbers were measured on the content in `content/demo/lower-bound`
  (version `c1d29a35f97d`), using g++ 14.2.0 under runc, with the
  `codeadapt-content validate` pipeline.
* **Proposed.** These candidate tests and bug models were measured the same way, in a
  scratch copy of the problem. Section 7 lists what changes. C1 and C2 (tests
  `pair_equal_target` and `absent_after_duplicates`, models E6–E8) were applied on
  2026-10-16; the rest of this record keeps the labels "candidate" and "new" for history.

Since this record was written, `problem.toml` gained the design declarations (test
`purpose` and `distinguishes`, E2's `known_limitation`, `[curriculum]`), which changes
the content version hash (`41dd7907bd39`); C1–C2 changed it again to `871602bc2bba`. The live
matrix is in [../content-reports/lower-bound.md](../content-reports/lower-bound.md).

Notation: `·` means the same output as the reference. `TLE` is the `time_limit`
signature. Numbers are the program's printed index.

## 1. Learning objective, designed backwards

**Concept.** Binary search for a *partition point*. On a sorted array, the predicate
`a[i] >= target` is false and then true. The task is to find the first true position,
which may be `n` (one past the end).

**Subskills.** These are the skill keys in `problem.toml`. They map to errors in
implementations, not to states of mind.

| Key | Subskill | What correct code must do |
| --- | --- | --- |
| `search_space_boundaries` | Bounds of the candidate range | Keep every possible answer, including `n`, inside `[lo, hi)`, and never discard `a[mid]` when it could be the answer. |
| `loop_termination` | Progress | Shrink the range on every iteration; the loop condition must match the interval convention. |
| `equality_handling` | Side of the boundary for equal elements | Send `a[mid] == target` left (keep searching for the *first* `>=`). |
| `problem_specification` | Returning what is asked | Return the boundary itself, `n` when absent above, never `-1` or a neighbouring index. |

**Prerequisites assumed.** Indexing a `std::vector`, `while` loops, integer division, the
meaning of "sorted, non-decreasing", and half-open versus closed intervals. Nothing in the
current bank exercises these on their own (see §6, gap G1).

**Not assessed, by design.** Midpoint overflow, because it needs more than 2^30 elements,
which is infeasible inside the memory limit. The O(log n) requirement is also not
assessed: a linear scan gives identical output (§4.4).

**Evidence of improvement on a later attempt.** For a diagnosed error of skill *S*, every
reliable test that probes *S* passes on the follow-up, and the follow-up is not diagnosed
with another error model of *S*. This is the criterion recorded in the
`recommendations.criterion` column (methodology §5). It is evidence about the follow-up's
tests, not about learning.

## 2. Plausible implementation errors

Each row is a pattern a student plausibly writes. It is listed whether or not we can
detect it.

| # | Error pattern | Modelled? | Skill | Measured behaviour (summary) |
| --- | --- | --- | --- | --- |
| E1 | `a[mid] <= target` instead of `<` (finds the upper bound) | yes: `upper_bound_confusion` | equality | Differs whenever the target is present. |
| E2 | `hi = n - 1` with a half-open loop | yes: `hi_init_last_index` | boundaries | Differs only when the answer is `n` (target above all elements). |
| E3 | `lo = mid` instead of `mid + 1` | yes: `no_progress_update` | termination | TLE whenever the search moves right with two candidates left. |
| E4 | Solves exact-match search (returns some match or `-1`) | yes: `exact_match_sentinel` | specification | `-1` when absent; any matching index when present. |
| E5 | Returns as soon as `a[mid] == target` | yes: `stops_at_first_match` | equality | Differs only with repeated targets. |
| E6 | `hi = mid - 1` in a half-open loop (discards a candidate) | candidate: `hi_skips_candidate` | boundaries | Off by one when `a[mid]` was the answer. |
| E7 | Closed loop `lo <= hi` with `hi = mid` | candidate: `closed_loop_hi_mid` | termination | TLE once `lo == hi`. |
| E8 | Closed-interval search returning `hi` instead of `lo` | candidate: `returns_wrong_pointer` | specification | Always one less than the answer. |
| E9 | Closed loop with `hi = n` (reads `a[n]`) | **not modellable** | boundaries | Undefined behaviour. The sanitizer flags it, the submission gets `UNRELIABLE_EVIDENCE` plus a safety finding, and it is never diagnosed. |
| E10 | Linear scan | **undetectable** | none | Identical output on every test. |
| E11 | Two errors at once (e.g. E1 + E2) | no | several | Outside the single-error space; abstains as `UNMODELLED_BEHAVIOUR` (confirmed on held-out `double_bug.cpp`). |
| E12 | `(lo + hi) / 2` overflow | no | boundaries | Not observable at feasible sizes. |

## 3. Test suite audit (as built, plus two proposed tests)

"Separates" lists the models whose output differs from the reference on that test. It
comes from the measured matrix in §4, not from intent.

| Test | Behaviour exercised | Expected | Separates from reference | Skills (via probes) | Why it is not redundant | Multi-cause risk |
| --- | --- | --- | --- | --- | --- | --- |
| `sample_present` | unique target, middle | 2 | E1, E3, E6*, E7*, E8* | equality | Visible to students; the first check most code meets. | High: five patterns fail it. |
| `sample_absent` | absent, between | 2 | E3, E4, E6*, E7*, E8* | specification | Visible absent case. | High. |
| `empty` | `n = 0` | 0 | E4, E8* | boundaries | Minimal case; where crashing variants (E9) fault. | Low. |
| `below_all` | answer 0, absent | 0 | E4, E7*, E8* | boundaries | Separates E7 from E3 (E3 passes here). | Low. |
| `above_all` | answer `n` | 3 | E2, E3, E4, E8* | boundaries, specification | One of only three tests that detect E2. | Medium. |
| `equal_first` | target at index 0 | 0 | E1, E7*, E8* | equality | Separates E1 from E3. | Low. |
| `equal_last` | target at `n-1` | 2 | E1, E3, E7*, E8* | equality | Same behaviour as `equal_first` at the other end. | Medium. |
| `duplicates_middle` | run of targets | 1 | E1, E3, E4, E5, E6*, E7*, E8* | equality | Main E5 evidence on a small input. | **Very high**: 7 patterns. |
| `duplicates_all` | every element equals target | 0 | E1, E4, E5, E7*, E8* | equality | Separates E5 from E6. | High. |
| `single_equal` | `n = 1`, equal | 0 | E1, E7*, E8* | boundaries, termination, equality | Minimal equality case. | Low. |
| `single_above` | `n = 1`, answer `n` | 1 | E2, E3, E4, E8* | boundaries, termination, specification | Minimal E2 case. | Medium. |
| `two_between` | `n = 2`, absent | 1 | E3, E4, E6*, E7*, E8* | termination, specification | Smallest input where E3 loops. | High. |
| `large_absent` | 200 000 elements | 50000 | E3, E4, E7*, E8* | termination, specification | Scale; same pattern as `two_between`. | High. |
| `large_above_all` | 200 000, answer `n` | 200000 | E2, E3, E4, E8* | termination, specification | Scale version of `above_all`. | Medium. |
| `large_duplicates` | 200 000 equal | 0 | E1, E4, E5, E7*, E8* | termination, equality | Scale version of `duplicates_all`. | High. |
| *`pair_equal_target`* (new) | `n = 2`, both equal | 0 | E1, E5, E7*, E8* | equality, termination | Gives E5 a small non-scale test (support 3 → 4). | Medium. |
| *`absent_after_duplicates`* (new) | absent, right of a run | 3 | E3, E4, E6*, E7*, E8* | specification | Gives E6 a test outside the "middle" cases. | High. |

\* models E6–E8, added by C2 on 2026-10-16 (first measured in scratch).

**Determinism.** Every reference and model output was identical across repeated runs,
and the sanitizer build found no undefined behaviour in the reference or the five
committed models. Validation enforces both.

**Redundancy found.** A *behaviour group* is a set of tests that every model either
passes together or fails together. It is measured from the matrix, not judged. With the
five committed models, the 15 tests fall into only 7 groups:

* `sample_present` and `equal_last`;
* `sample_absent`, `two_between` and `large_absent`;
* `empty` and `below_all`;
* `above_all`, `single_above` and `large_above_all`;
* `equal_first` and `single_equal`;
* `duplicates_all` and `large_duplicates`;
* `duplicates_middle` on its own.

Redundancy depends on which models exist. With the candidate models and the two
proposed tests, the 17 tests fall into 11 groups. For example, E7 separates
`below_all` from `empty`.

**The most important finding.** The `min_support = 2` rule counts *tests*, not
*independent behaviours*. All three tests that support `hi_init_last_index` (E2) exercise
the same single behaviour, "the answer is `n`". So E2's support of 3 is really one behaviour group, and it overstates how independent
its evidence is. Any other error that cannot return `n` would produce the
same three failures, for example `return min(lo, n - 1)`. We have not modelled that
error, so a student who writes it would currently be diagnosed with E2. That is a
plausible false positive the held-out set does not test (§4.3).

## 4. Discrimination matrix (measured)

Columns: E1 `upper_bound_confusion`, E2 `hi_init_last_index`, E3 `no_progress_update`,
E4 `exact_match_sentinel`, E5 `stops_at_first_match`, E6 `hi_skips_candidate`,
E7 `closed_loop_hi_mid` and E8 `returns_wrong_pointer`. E6–E8 and the two starred tests
were added by C1–C2 on 2026-10-16 (content version `871602bc2bba…`); the generated
[report](../content-reports/lower-bound.md) is the authoritative copy of this matrix.

| Test | Ref | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sample_present | 2 | 3 | · | TLE | · | · | 1 | TLE | 1 |
| sample_absent | 2 | · | · | TLE | -1 | · | 1 | TLE | 1 |
| empty | 0 | · | · | · | -1 | · | · | · | -1 |
| below_all | 0 | · | · | · | -1 | · | · | TLE | -1 |
| above_all | 3 | · | 2 | TLE | -1 | · | · | · | 2 |
| equal_first | 0 | 1 | · | · | · | · | · | TLE | -1 |
| equal_last | 2 | 3 | · | TLE | · | · | · | TLE | 1 |
| duplicates_middle | 1 | 5 | · | TLE | 2 | 3 | 0 | TLE | 0 |
| duplicates_all | 0 | 7 | · | · | 3 | 3 | · | TLE | -1 |
| single_equal | 0 | 1 | · | · | · | · | · | TLE | -1 |
| single_above | 1 | · | 0 | TLE | -1 | · | · | · | 0 |
| two_between | 1 | · | · | TLE | -1 | · | 0 | TLE | 0 |
| large_absent | 50000 | · | · | TLE | -1 | · | · | TLE | 49999 |
| large_above_all | 200000 | · | 199999 | TLE | -1 | · | · | · | 199999 |
| large_duplicates | 0 | 200000 | · | · | 99999 | 100000 | · | TLE | -1 |
| pair_equal_target* | 0 | 2 | · | · | · | 1 | · | TLE | -1 |
| absent_after_duplicates* | 3 | · | · | TLE | -1 | · | 2 | TLE | 2 |

\* added by C1 (2026-10-16), appended so earlier test numbers are unchanged.

### 4.1 Separation from the reference (number of detecting tests)

| | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Original 15 tests | 7 | 3 | 9 | 11 | 3 | 4 | 12 | 15 |
| All 17 tests (current) | 8 | 3 | 10 | 12 | 4 | 5 | 13 | 17 |
| Behaviour groups behind them (committed models, 15 tests) | 4 | **1** | 4 | 5 | **2** | — | — | — |
| Behaviour groups (all 8 models, 17 tests; current) | 6 | **1** | 6 | 7 | 3 | 3 | 9 | 11 |

Behaviour groups are defined in §3. E2 rests on a single group whatever is added, and E5
rests on tests that all contain repeated targets. More tests cannot fix E2: an unmodelled
error that clamps the answer to `n - 1` produces exactly E2's outputs on every input, so
the two are indistinguishable by behaviour, and E2 stays a documented limitation. E5's
three groups are all "repeated target" inputs, so they separate E5 from the other models
but not from other duplicate-handling errors (§4.3).

### 4.2 Pairwise separation

There are no identical pairs, either among the five committed models or with the
candidates. The weakest pairs are:

* **E2 and E5:** 7 distinguishing tests (6 before C1). Both pass most tests,
  but they fail *disjoint* sets of tests, so they are never confused with each other.
* **E3 and E7:** both produce TLE, but on different tests. `below_all`, `equal_first`,
  `single_equal` and `duplicates_all` loop only for E7; `above_all` and `single_above`
  loop only for E3. So they are separable by *where* the loop hangs. The TLE signature
  alone is not specific to any error: any infinite loop or very slow algorithm produces it.

### 4.3 Collisions with unmodelled errors (analysed, not measured)

| Unmodelled error | Collides with | Consequence | Mitigation |
| --- | --- | --- | --- |
| `return min(lo, n - 1)` (clamps the end) | E2 on all three tests | False E2 diagnosis | **Corrected by measurement (calibration, 2026-10-15).** Written naturally, the clamp returns `-1` on the empty array, which separates it from E2 (`UNMODELLED_BEHAVIOUR`). With an `if (a.empty()) return 0;` guard it is indistinguishable from E2 on every test and *is* diagnosed as E2 by v1. No input separates the guarded form. **Preserve the ambiguity:** diagnoses of E2 are now reported as qualified (ADR-019), E2's hint ("can your search ever return `a.size()`?") fits either cause, and the follow-up targets the skill rather than the specific bug. |
| Any infinite loop elsewhere | E3 or E7 | A false termination diagnosis is possible if the loop happens on exactly E3's tests | Low risk: E3's pattern is specific (moving right with 2 candidates). Held-out cases for loops written in other styles are needed. |
| Off-by-one only on duplicates (e.g. returns the last of a run) | E1 on duplicate tests | Separated by `equal_first` and `single_equal`, where E1 fails but this error does not | Already covered: strict consistency gives `UNMODELLED_BEHAVIOUR`. |

### 4.4 Errors the suite cannot see

* **Linear scan (E10).** Measured: identical to the reference on all 17 tests, and
  `codeadapt-content validate` rejects it as undetectable. The 200 000-element tests run
  fast either way, and timing includes container start-up, so wall time cannot separate
  O(n) from O(log n). **Unsupported.** The statement's O(log n) rule is not enforced, and
  no diagnosis should claim it is.
* **Reading `a[n]` (E9).** Measured: crashes (`signal 11`) on `empty`, and silently prints
  plausible numbers on the other above-all tests. The sanitizer reports
  `heap-buffer-overflow`, so validation rejects it as a model and student code like it is
  routed to `UNRELIABLE_EVIDENCE` with a safety finding. This is intended: plausible
  numbers from undefined behaviour are not evidence.

## 5. From evidence to concepts

| Observed (reliable tests) | Candidate hypotheses | Skill implicated | Strength of evidence | Limitation | Next activity |
| --- | --- | --- | --- | --- | --- |
| Fails only "answer is `n`" tests (`above_all`, `single_above`, `large_above_all`) | E2; unmodelled "clamp to n-1" | boundaries | **Weak**: one behaviour, three tests | Cannot separate E2 from other "can't return n" errors | Practice that needs the end position as an answer in a *different* context (count-occurrences, run at the end). Criterion: its `run_at_end` tests pass. |
| Fails equal-target tests, including `equal_first` | E1 | equality | Strong: 3 behaviours | — | count-occurrences (9 equality tests). |
| Fails only with repeated targets | E5, or an unmodelled duplicate error | equality | **Weak**: every test has a repeated target | Every failing test has duplicates | count-occurrences (duplicates at start/middle/end). |
| TLE on the "move right" tests | E3 | termination | Medium: pattern-specific, but TLE is non-specific | Slow or looping code elsewhere can mimic it | A termination-focused exercise (gap G2). Meanwhile: last-less-than. |
| `-1` on absent tests | E4 | specification | Strong: 4 behaviours | — | last-less-than (its spec *does* return -1, which forces reading the spec). |
| Matches two models | Ambiguous | the union | None for either one alone | Do not pick | A problem whose suite separates those skills (policy v1 `AMBIGUOUS` rule). |
| Matches no model | Unmodelled | **none claimed** | — | Do not invent a concept | Retry with test feedback; flagged for research review. |
| All pass | — | — | Passing *these* tests | Says nothing about transfer | An equivalent problem not yet passed (policy v1), then a transfer problem (gap G3). |

**Gap found in the implementation, now fixed (C5, ADR-019).** The evidence ledger
(`adaptation/ledger.py`) attributed *every* failing test to every skill its probes name,
whether or not a diagnosis explained the failure. Policy v1 only used the ledger to
*count* evidence when ranking problems, so nothing wrong was shown to students, but it
contradicted the rule above. Since policy 1.1 a failure is skill evidence only when a
supported diagnosis explains it, and only for that model's skill.

## 6. Follow-up and curriculum links

| Relation | Current bank | Gap |
| --- | --- | --- |
| Prerequisite | none | **G1**: "first true in a boolean array" (a partition point with no equality subtlety) and "linear lower bound" (specification without search) |
| Equivalent practice | count-occurrences, last-less-than | — |
| Termination-focused practice | none | **G2**: a search where the right-moving update is the only hard part (e.g. integer square root, a search over the answer space) |
| Transfer (harder) | none | **G3**: search over an answer space (minimum feasible value), search in a rotated array |
| Reassesses earlier skills | — | Lower-bound reassesses nothing yet: it is the root of the family |

Recommendation behaviour this design needs, compared with policy v1 today:

* Boundary error (E2, E6) → practice the same skill in another context, where the
  criterion probes the end position. v1 does this.
* Ambiguous → a problem that *separates* the candidate skills. v1 ranks by modelled skills,
  which is a proxy. A purpose-built discriminating exercise would be better.
* Correct, little transfer evidence → an independent problem of similar difficulty, then
  G3. v1 picks the least-evidenced problem not yet passed.
* Unmodelled → no concept claim, retry. v1 does this.
* Prerequisite weak (repeated failures across the family on the same skill, with
  diagnoses) → step back to G1, not up in difficulty. **v1 cannot do this yet**: there
  are no prerequisite links or prerequisite problems.

## 7. Changes this design proposes for lower-bound

| ID | Change | Why | Measured effect |
| --- | --- | --- | --- |
| C1 | Add tests `pair_equal_target`, `absent_after_duplicates` | Small-input evidence for E5 and E6 | E5 support 3 → 4; E6 4 → 5; no new collisions |
| C2 | Add models E6 `hi_skips_candidate`, E7 `closed_loop_hi_mid`, E8 `returns_wrong_pointer` | Common closed-versus-half-open mix-ups | All deterministic, UB-free, and separable from every other model |
| C3 | Do **not** add E9 or E10 as models | E9 is undefined behaviour; E10 is undetectable | Validation rejects both |
| C4 | Record test purpose and intended discrimination in `problem.toml`, and have validation compare them with the measured matrix | Turns §3 into a checked artefact, not prose | Tooling change |
| C5 | Ledger: record only diagnosis-explained outcomes as skill evidence | §5 gap | Changes adaptation inputs; needs an ADR and re-running the trajectories |
| C6 | Diagnosis v2 candidate: count support by *distinct behaviour groups* rather than tests | §3 key finding (E2, E5) | Would turn E2 and E5 diagnoses into `INSUFFICIENT_EVIDENCE` unless more behaviours are added. Must be compared with v1 on the held-out set before adoption |

**Status after the owner's review (2026-10-15).** C3, C4 and C5 are done. C6 was
measured against v1 on the held-out and calibration sets and awaits an owner decision; the
deployed method reports single-behaviour diagnoses as qualified instead.

**C1 and C2 applied (2026-10-16, owner approval).** Each new model is a one- to three-line
change from the reference (sources in `content/demo/lower-bound/error_models/`), and its
measured behaviour matches the intended error: E6 discards a candidate answer (wrong output
on 5 tests), E7 loops forever whenever the search ends on an element `>= target` (TLE on
13 tests), and E8 returns `lower_bound - 1` on every test. Validation with 3 repeats
reported every model deterministic, sanitizer-clean, and separable from every other model,
and every declared `distinguishes` agrees with the measurement. The content version
changed from `41dd7907bd39…` to `871602bc2bba…`; submissions record the version they were
diagnosed against, so earlier submissions stay tied to the old fingerprints.

## 8. Known limitations of this problem as an instrument

* E2's diagnosis rests on a single behaviour group (documented as `known_limitation`, and
  reported to students as one possible cause), and E5's rests only on inputs with
  repeated targets. These are the diagnoses most likely to be wrong on real code.
* The O(log n) requirement is stated but not assessed.
* Uninitialised reads are not detected (no MSan in GCC).
* The skill mapping is an author's modelling assumption. It has not been validated
  against expert labels on real submissions (methodology §6.2).
* The held-out cases were written by the same author as the models, and some are close
  to them (`classic_exact_search.cpp` is the same algorithm as E4).
