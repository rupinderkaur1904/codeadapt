# L20 alternative-cause search: the four original problems (2026-10-26)

**Status.** Investigation only (owner request D, 2026-10-26).

**Nothing was changed because of this search.** No fingerprint, skill mapping,
`known_limitation`, content version or evidence rule was changed. Any change needs a separate
owner decision.

> **Update 2026-10-26 (ADR-037).** On the owner's later request the S1 safeguard was applied
> to the four clear-cut cases O1–O4 (§2.1); see l20-original-s1.md. The contestable (§2.2)
> and unsupported (§2.3) cases are unchanged. This record is otherwise kept as written.

**Problems searched:** lower-bound, count-occurrences, last-less-than and first-true. These
four were left out of docs/reviews/2026-10-25/l20-search.md (§4.5 there).

## 1. Method

The method is the one in l20-search.md §2, unchanged.

**Which models matter.** Only models that v1.3 can name unqualified matter. These are
excluded:

- **Time limit (rule 4b):** lower-bound `no_progress_update` and `closed_loop_hi_mid`,
  `no_progress_update` in count-occurrences and last-less-than, and first-true
  `no_progress_update` and `closed_loop_hi_mid`.
- **Constant output (rule 8a):** count-occurrences `upper_uses_strict`, which always
  returns 0.
- **Qualified:** `hi_init_last_index` in all four problems. It has one behaviour group and
  a `known_limitation`, and its collision with a clamping program was already documented.

That leaves **15 nameable models**: 5 in lower-bound, 1 in count-occurrences, 3 in
last-less-than and 6 in first-true.

**Alternatives.** 17 complete programs, in `l20-search-original/<problem>/`. Each file's
header states:

- its cause;
- the skill that cause would belong to (my classification);
- the model it targets.

**Runs.** Each program, the reference and every model run on the problem's committed tests
and on two domains. The builds are native g++ -O2 with libstdc++ assertions. The fork-per-call
driver is the one from 2026-10-25, with a 0.5 s timer.

| Problem | Exhaustive small domain | Seeded random domain (3 000 inputs, seed 20261026) |
| --- | --- | --- |
| lower-bound, count-occurrences, last-less-than | every non-decreasing array of length 0–6 over {0..3}, every target −1..4 (1 260 inputs) | length 0–40, values −30..30, target −35..35 |
| first-true | every valid flags array of length 0–12 (91 inputs) | length 0–200, random split point |

**Reproduce** (from the repository root; needs g++; about 2 minutes):

```
python3 docs/reviews/2026-10-26/l20-search-original/search.py [problem ...]
```

The output is committed as `l20-search-original/results.txt`.

**Limits.**

- Native runs approximate the sandbox; the authoritative fingerprints are in
  docs/content-reports/.
- The domains are bounded. Zero differences is an observed equivalence on them, **not a
  proof.** Where a one-line argument makes the equivalence exact, it is given below.
- The cause classification is mine, and no second reviewer has checked it.
- Nothing here measures diagnostic accuracy.

## 2. Results

Columns give differing outputs against the model: committed tests (15–19), then exhaustive /
random.

### 2.1 Clear-cut cross-skill equivalences: 4 models

These follow the pattern of the 11 cases the owner approved for S1 on 2026-10-26:

- the model's input–output function is a correct solution to a plausible misreading of the
  task; or
- it is the same answer-variable initialisation error that was classified as
  `search_space_boundaries` in l20-search.md case 4.

| # | Problem | Model (mapped skill) | Alternative (cause; its skill) | Tests | Domains | Why they agree |
| --- | --- | --- | --- | --- | --- | --- |
| O1 | lower-bound | `upper_bound_confusion` (equality_handling) | `first_gt_by_spec`: task read as "first element > target" (problem_specification) | 0 | 0 / 0 | Both compute the upper bound |
| O2 | last-less-than | `uses_le` (equality_handling) | `last_le_by_spec`: task read as "last element ≤ target" (problem_specification) | 0 | 0 / 0 | Both return upper bound − 1 |
| O3 | last-less-than | `clamps_to_zero` (problem_specification) | `answer_starts_zero`: answer variable starts at 0 instead of −1 (search_space_boundaries) | 0 | 0 / 0 | Both return max(lower bound − 1, 0) |
| O4 | first-true | `none_sentinel` (problem_specification) | `answer_var_starts_minus_one`: searches [0, n − 1] with the answer variable at −1 (search_space_boundaries) | 0 | 0 / 0 | Both return −1 exactly when there is no 1 |

### 2.2 Contestable cross-skill equivalences: 4 models

Each is cross-skill only if the alternative's cause belongs to a different skill, and that is
open to argument. Three are the same kind as the 2026-10-25 contestable cases #3 and #13:
which end of the final interval to return, or which value to record. Those two cases are
analysed in docs/reviews/2026-10-26/l20-contestable-cases.md.

| # | Problem | Model (mapped skill) | Alternative (cause; its skill) | Tests | Domains | Why they agree |
| --- | --- | --- | --- | --- | --- | --- |
| O5 | lower-bound | `returns_wrong_pointer` (problem_specification) | `half_open_returns_lo_minus_one`: returns lo − 1 at exit (loop_termination?) | 0 | 0 / 0 | Both return lower bound − 1 |
| O6 | last-less-than | `returns_insertion_point` (problem_specification) | `answer_records_next`: the answer variable records mid + 1 (an update error; as case #13) | 0 | 0 / 0 | Both return the lower bound |
| O7 | first-true | `returns_last_false` (problem_specification) | `closed_returns_hi`: closed loop returns hi at exit (loop_termination?; as case #3) | 0 | 0 / 0 | At exit hi = lo − 1 |
| O8 | lower-bound | `stops_at_first_match` (equality_handling) | `match_or_insertion_half_open`: task read as "any copy of the target, else the insertion point" (problem_specification) | 0 | 0 / 0 | The same code |

**O5 is evidence about case #3.** The model itself is "a correct closed-interval search that
returns hi". That is the cause the 2026-10-25 search attributed to `loop_termination` in
upper-bound `closed_returns_hi`. This bank maps that cause to `problem_specification`
(lower-bound, since the model was added in commit 777434f). Under that mapping, O5, O7 and case #3 are
same-skill equivalences.

**O8 depends on the implementation.** The natural closed-interval program for the same
reading, `match_or_insertion_closed`, differs from the model:

- on 3 committed tests;
- on 194 / 1 260 exhaustive inputs;
- on 97 / 3 000 random inputs.

It returns a different copy of the target when values repeat. Only the program that shares
the model's exact loop is a twin. The reading is also a compound one ("any copy, else the
insertion point"), which is less plausible than the single misreadings in §2.1.

### 2.3 Unsupported equivalences: 2 models

**An equivalent program exists for each, but its cause is not a plausible, distinct cause.**
These are not proposed for any safeguard.

| # | Problem | Model (mapped skill) | Equivalent program | Tests | Domains | Why it does not count |
| --- | --- | --- | --- | --- | --- | --- |
| O9 | first-true | `lo_init_one` (search_space_boundaries) | `zero_read_as_absent`: correct search, then replaces a result of 0 by 1 | 0 | 0 / 0 | No plausible reading of the task gives this; written only to test whether the behaviour max(first 1, 1) has another program |
| O10 | first-true | `hi_skips_candidate` (search_space_boundaries) | `half_open_hi_minus_one_closed_exit` | 0 | 0 / 0 | Its extra guard (`mid == lo`) is a no-op: when it fires, the model also ends with lo = mid. It still discards the candidate with hi = mid − 1, so its cause is the model's cause. The header's loop_termination label is not supported |

### 2.4 Same-skill equivalences

These agree on both domains, but the alternative's cause belongs to the model's skill, so
the attribution is unaffected.

| Problem | Model | Alternative |
| --- | --- | --- |
| lower-bound | `returns_wrong_pointer` | `last_below_by_spec` |
| count-occurrences | `inclusive_count` | `closed_interval_length`, `open_lower_returns_lo` |
| last-less-than | `returns_insertion_point` | `first_ge_by_spec` |
| first-true | `returns_last_false` | `last_zero_by_spec` |

### 2.5 No equivalent found among the alternatives tried: 4 models

| Problem | Model | Closest alternative | Differences (tests; exhaustive / random) |
| --- | --- | --- | --- |
| lower-bound | `exact_match_sentinel` | `first_match_or_sentinel_by_spec` (problem_specification) | 3; 142 / 76 |
| lower-bound | `hi_skips_candidate` | none: `closed_updates_stops_early` turned out correct (0 failures on tests and both domains) | — |
| first-true | `returns_any_true` | `any_one_closed_by_spec` (problem_specification) | 6; 37 / 1 846 |
| first-true | `stops_one_early` | `open_template_lo_zero` (search_space_boundaries) | 18; 90 / 2 980 |

"No equivalent found" means none of the programs tried was equivalent. It does not show that
none exists.

## 3. Summary

| | Models |
| --- | --- |
| Nameable models searched | 15 |
| Clear-cut cross-skill twin (§2.1) | 4 |
| Contestable cross-skill twin (§2.2) | 4 |
| Equivalent program, unsupported cause (§2.3) | 2 |
| Only same-skill twins (§2.4) | 1 (count-occurrences `inclusive_count`) |
| No equivalent found (§2.5) | 4 |

- **The 2026-10-25 pattern recurs.** Wherever a model's behaviour equals a clean
  specification of a nearby task, a twin exists. O1 and O2 are the `equality_handling`
  version of cases #1 and #7. O3 and O4 are the answer-variable version of case #4.
- **The contestable cases share one question:** is "which variable to return or record at
  the end" a `problem_specification` error? The bank already answers yes in lower-bound
  `returns_wrong_pointer`. The contestable-case analysis recommends keeping that reading
  (l20-contestable-cases.md).
- **Possible next step, not taken.** O1–O4 could take the S1 route: a `known_limitation`
  per model and new content versions. That is an owner decision. Until then, these four
  models still give `incorrect` observations when named unqualified.

## 4. Recheck of the 2026-10-25 search script

While extending the script I found an input-mode gap. `search.py` (2026-10-25) expands only
the L, A and D input modes. As a result:

- the rotated-search R mode and the peak-index M mode (4 large committed tests each) were
  passed to the driver unexpanded;
- the "Tests" column for those two problems did not run those 4 tests as intended.

The domain columns, the main evidence, were not affected.

**Recheck.** `l20-search-recheck/search_all_modes.py` is a copy that differs only in
expanding R and M. Its output is `l20-search-recheck/results.txt`, and the reproduce command
is:

```
python3 docs/reviews/2026-10-26/l20-search-recheck/search_all_modes.py rotated-search peak-index
```

- **The equivalences are unchanged.** Every "identical on all tests to" result is the same
  as in the original run, including the S1 cases #10 (rotated-search
  `left_range_excludes_lo`) and #11 (peak-index `swapped_direction`).
- **Some counts change** for pairs that were already separable:
  - the per-alternative failure counts;
  - the test-difference counts of the non-equivalent pairs, for example peak-index
    `hi_starts_second_last` vs `stops_one_early`, 5 → 7.

The 2026-10-25 script and its results.txt are kept unchanged as the record. The new script
for the four original problems expands every mode they use: L, A and D, plus first-true's P.
