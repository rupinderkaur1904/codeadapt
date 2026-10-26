# L20 alternative-cause search: six provisional binary-search problems (2026-10-25)

**Status.** Review evidence for the owner (approved action 3, 2026-10-25 13:27).

**Update 2026-10-26 (added; the record below is unchanged).**
- **S1 approved and applied** to the 11 clear-cut models (ADR-036).
- **Contestable cases #3 and #13** are analysed in docs/reviews/2026-10-26/l20-contestable-cases.md.
  Both are unchanged.
- **The four original problems** were searched in docs/reviews/2026-10-26/l20-search-original.md.
- **Input-mode gap.** The script below did not expand the rotated-search R and peak-index M
  input modes for committed tests. The rerun in that report's §4 leaves every equivalence
  here unchanged. Only some failure and test-difference counts for already-separable pairs
  differ.

**No fingerprint, skill mapping, `known_limitation`, content file or rule was changed.** The
safeguards in §5 are proposals.

**Problems searched:** upper-bound, exact-search, last-occurrence, rotated-search, peak-index
and integer-sqrt. min-capacity and rotated-min were reviewed earlier
(skill-mapping-review.md).

## 1. Question

When v1.3 names an error model unqualified, the attempt gives one `incorrect` observation on
that model's skill. Could a program with a **different cause**, preferably one belonging to a
different skill, produce the same output on every test, so that the model would be named for
it? And is that sameness an artefact of the tests, or an equivalence on the input domain?

## 2. Method (the L20 method, extended)

**1. Which models matter.** Only models that v1.3 can name unqualified matter:

- **Excluded by rule 4b (ADR-027), time limit:**
  - upper-bound `no_progress_update` and `closed_loop_hi_mid`;
  - `no_progress_update` in exact-search, last-occurrence and peak-index;
  - integer-sqrt `floor_mid_no_progress`.
- **Excluded as qualified (`known_limitation` and one behaviour group):** last-occurrence
  `missing_equality_check` and rotated-search `left_half_test_strict`.
- **The rest, 29 models,** can be named unqualified.

The script reads these facts from the sandbox reports in docs/content-reports/.

**2. Alternatives.** Each one is a complete program written to have a different cause from a
target model, preferably a cause that belongs to a different skill. There are 26 programs,
in `l20-search/<problem>/`. Each file's header states its cause, the skill it would belong
to, and the model it targets. One turned out to be correct (§4.4).

**3. Committed tests.** Every program, the reference and every model run on the problem's
committed tests:

- natively, with g++ -O2 and libstdc++ assertions;
- through a fork-per-call driver (`driver.cpp`) with a 0.5 s timer, so non-termination
  shows as TLE and a crash as RE.

A model with the same output as the alternative on every test is the model v1.3 would
consider.

**4. Domains.** The alternative and that model are then compared on two domains.

| Problem | Exhaustive small domain | Seeded random domain (3 000 inputs, seed 20261025) |
| --- | --- | --- |
| upper-bound, last-occurrence | every non-decreasing array of length 0–6 over {0..3}, every target −1..4 (1 260 inputs) | length 0–40, values −30..30 |
| exact-search | every strictly increasing array of length 0–6 over {0..7}, every target −1..8 (2 470) | length 0–40, distinct values −100..99; target present or random |
| rotated-search | every rotation of every strictly increasing array of length 1–6 over {0..6}, every target −1..7 (3 969) | length 1–40; target present or random |
| peak-index | every strict mountain array of length 1–6 over {0..5} (941) | length 1–40, random peak position |
| integer-sqrt | every x in 0..200 000, plus k²−1, k², k²+1 for every k ≤ 46 340, plus 2³¹−1 (337 681) | uniform on 0..2³¹−1 |

**What the outcome means.** Zero differences on both domains is an observed equivalence on
those domains. **It is evidence, not proof** that the two programs agree on every valid input.
For most of the equivalences below a one-line argument makes them exact, and it is given.

**Approximation.** Native runs approximate the sandbox, which also uses a sanitizer build
and a repeat; the authoritative fingerprints are in docs/content-reports/. The skill a cause
"belongs to" is my judgement, stated per file and in the tables, and two are marked
contestable.

**Reproduce:**

```
python3 docs/reviews/2026-10-25/l20-search/search.py [problem ...]
```

It needs g++ and takes about 25 minutes, mostly integer-sqrt. The output is committed as
`l20-search/results.txt`.

## 3. Results

Every model below would be named unqualified by v1.3. The "Tests" and "Domains" columns give
the number of differing outputs: committed tests (out of 16–21), then exhaustive / random.

### 3.1 Cross-skill equivalences: 13 models

| # | Problem | Model (mapped skill) | Alternative (cause; its skill) | Tests | Domains | Why they agree |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | upper-bound | `lower_bound_confusion` (equality_handling) | `first_ge_answer_var`: task read as "first element ≥ target" (problem_specification) | 0 | 0 / 0 | Both compute the lower bound |
| 2 | upper-bound | `hi_init_last_index` (search_space_boundaries) | `clamps_to_valid_index`: correct search, result clamped to n − 1 "to be a valid index" (problem_specification) | 0 | 0 / 0 | Both return min(upper bound, n − 1), and 0 for an empty array |
| 3 | upper-bound | `returns_last_not_greater` (problem_specification) | `closed_returns_hi`: closed loop returns `hi` at exit (loop_termination; **contestable**) | 0 | 0 / 0 | At exit `hi = lo − 1` |
| 4 | upper-bound | `none_sentinel` (problem_specification) | `answer_var_starts_minus_one`: searches only [0, n − 1] with the answer variable starting at −1 (search_space_boundaries) | 0 | 0 / 0 | Both return −1 exactly when the upper bound is n |
| 5 | exact-search | `swapped_direction` (search_space_boundaries) | `assumes_descending`: array read as decreasing (problem_specification) | 0 | 0 / 0 | The same comparisons with the branches exchanged |
| 6 | exact-search | `lo_init_one` (search_space_boundaries) | `zero_index_as_not_found`: correct search, but index 0 used as "false" (problem_specification) | 0 | 0 / 0 | Both differ from the reference only when the target is at index 0 |
| 7 | last-occurrence | `returns_first_occurrence` (equality_handling) | `first_occurrence_by_spec`: task read as "first occurrence" (problem_specification) | 0 | 0 / 0 | Both compute the first occurrence |
| 8 | last-occurrence | `stops_at_any_match` (equality_handling) | `any_match_by_spec`: task read as "any occurrence" (problem_specification) | 0 | 0 / 0 | The same textbook exact search |
| 9 | last-occurrence | `hi_init_last_index` (search_space_boundaries) | `clamps_bound`: correct upper bound clamped to n − 1 (problem_specification) | 0 | 0 / 0 | The same as #2, followed by the same check |
| 10 | rotated-search | `left_range_excludes_lo` (equality_handling) | `lo_plus_one_left_range`: treats a[lo] as already examined (search_space_boundaries, **not declared** for this problem) | 0 | 0 / 0 | Both exclude a target equal to a[lo] from the left half |
| 11 | peak-index | `swapped_direction` (search_space_boundaries) | `finds_valley_by_spec`: task read as "find a minimum" (problem_specification) | 0 | 0 / 0 | The same comparison |
| 12 | integer-sqrt | `strict_square_test` (equality_handling) | `largest_square_below_by_spec`: "largest r with r² < x"; and `sqrt_of_x_minus_one`: floor √(x − 1) (both problem_specification) | 0 | 0 / 0 | All three compute ⌈√x⌉ − 1, and 0 at x = 0 |
| 13 | integer-sqrt | `returns_lo_closed` (problem_specification) | `answer_records_next`: the answer variable records mid + 1 (an update or loop error; **contestable**) | 0 | 0 / 0 | Both return ⌊√x⌋ + 1 |

The integer-sqrt equivalence in #12 is not visible on the random domain, which contains no
perfect squares. Only the exhaustive domain exercises it: the 46 340 differences from the
reference are exactly the perfect squares.

### 3.2 Same-skill equivalences: 6 models

These agree on both domains, but the alternative's cause belongs to the same skill, so the
attribution is unaffected.

| Problem | Model | Alternative |
| --- | --- | --- |
| exact-search | `returns_insertion_point` | `lower_bound_no_check` |
| last-occurrence | `returns_one_past` | `one_based_result` |
| rotated-search | `returns_sorted_position` | `min_then_sorted_position` |
| peak-index | `returns_value` | `value_by_spec` |
| integer-sqrt | `returns_ceiling` | `ceiling_by_rounding` |
| integer-sqrt | `hi_cap_46340` | `cap_at_root_of_int_max` |

### 3.3 No equivalent found among the alternatives tried: 8 models

| Problem | Model | Closest alternative | Differences (tests; exhaustive / random) |
| --- | --- | --- | --- |
| upper-bound | `hi_skips_candidate` | `closed_skips_on_greater` | 4; 329 / 1 397 |
| exact-search | `closed_loop_lt` | `halfopen_hi_last` (search_space_boundaries) | 3; 238 / 947 |
| rotated-search | `closed_loop_lt` | `hi_starts_second_last` | 4; 441 / 1 063 |
| rotated-search | `ignores_rotation` | `assumes_sorted` | 5; 301 / 251 |
| peak-index | `stops_one_early` | `hi_starts_second_last` | 5; 288 / 1 145 |
| integer-sqrt | `closed_loop_lt` | `halfopen_loop_running_answer` | 8; 140 475 / 1 250 |
| integer-sqrt | `hi_excludes_x` | `small_x_special_case` (problem_specification) | 1 test (x = 0); 1 / 0 |
| peak-index | `hi_skips_candidate` | none: `closed_answer_left_shift` turned out correct (§4.4) | — |

**Not attempted:** exact-search `returns_value` and integer-sqrt `fixed_iterations_16`.
"No equivalent found" means none of the programs tried was equivalent. It does not show that
none exists.

**integer-sqrt `hi_excludes_x` is separable only by x = 0.** The specification-cause program
fails only x = 1, while the model also returns −1 at x = 0. So the committed `zero` test
separates them, and the model has no known twin.

## 4. Findings

### 4.1 Most named diagnoses in these problems are not unique by skill

13 of the 29 nameable models (45%) have a cross-skill twin on both domains. 11 of these are
clear-cut; #3 and #13 depend on a contestable classification of the alternative's cause.
Every one of the 13 would currently put an `incorrect` observation on the mapped skill.

### 4.2 The pattern is systematic

Twelve of the thirteen twins are of one kind: the model's input–output function is itself a
natural reading of a different task. Examples:

- "first ≥" instead of "first >";
- "first occurrence" instead of "last occurrence";
- "a valid index" instead of "n allowed";
- "descending" instead of "ascending".

A student who misreads the task writes a correct program for that reading, and it has the
model's behaviour. Wherever a model's behaviour equals a clean specification of another
task, a `problem_specification` twin exists. **No test can separate the two.**

### 4.3 The skill keys name causes, and tests observe behaviour

`equality_handling`, `search_space_boundaries` and `loop_termination` describe causes in the
code. The tests observe only the function the code computes. This matches the min-capacity
finding (ADR-032) and the owner principle that the system must not claim to distinguish
observationally indistinguishable causes. It is also an input to the taxonomy proposal
(docs/proposals/l22-skill-taxonomy.md §3).

### 4.4 One alternative was correct

`peak-index/closed_answer_left_shift.cpp` was intended as a wrong program, but it agrees with
the reference everywhere. The file is kept, with its header corrected, as a record of the
attempt. It is not a finding about the tests.

### 4.5 Scope

- **Problems.** The four original problems were not searched in this action. lower-bound
  `hi_init_last_index` is already a documented collision with a clamping program, and the
  pattern in §4.2 suggests that others exist.
- **Domains.** Native runs on bounded domains, not proofs.
- **Classification.** The cause classification is mine.
- **Accuracy.** Nothing here measures diagnostic accuracy. The question is only whether an
  attribution can be unique.

## 5. Proposed safeguards (for review; none applied)

**S1. Recommended: the existing ADR-032 route, per model.** Add a documented
`known_limitation` to the 11 clear-cut models (#1, #2 and #4–#12).

- **Effect on diagnosis.** Diagnoses are still made and traced. Feedback becomes "other
  mistakes can produce the same pattern".
- **Effect on evidence.** No `incorrect` observation and no BKT update. The recommendation
  keeps `qualified_hypothesis`, exactly as for min-capacity.
- **What it needs:**
  - one sentence per model in its `problem.toml`;
  - new content versions for the six problems (earlier versions keep their snapshots,
    ADR-023 D4);
  - re-measured fingerprints and reports;
  - a unit test per model, like `test_non_unique_attributions_are_documented_collisions`.
- **Code.** None.
- **Decision for you:** #3 and #13, the contestable cases. Treat them the same, or leave them
  until a second reviewer classifies the alternatives.

**S2. Alternative: one switch for unreviewed problems.** While a problem is unaccepted (all
six are), its diagnoses give no `incorrect` evidence.

- It covers undiscovered twins too, and is fully reversible.
- It is a new evidence rule with code, so it is a larger change than S1. It would also
  withhold evidence from the 16 nameable models that have no known cross-skill twin.

**S3. Process safeguard, whichever of S1 or S2 is chosen.** Make the §4.2 check a required
step before admitting a model:

> Is this model's behaviour a correct solution to a plausible misreading of the task?

If yes, the model is admitted only with a `known_limitation` or a `problem_specification`
mapping. This is a design-record checklist item, not code.

**Not proposed: adding tests.** The equivalences are exact on the valid domain, so no test can
separate these pairs.
