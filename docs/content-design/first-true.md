# Content design record: `first-true` (CE1.1, gap G1)

**Status.** The design record was committed (`89a7803`) before the problem's content was
measured and before any held-out case was run. §4.2 and §7 were completed after
measurement. The matrix in §4 is a **design-time prediction**: a
Python re-implementation of each planned model, used to choose tests. It is not the
sandbox measurement. The measured matrix is added in §4.2 after validation, and wherever
the two disagree, the measurement wins.

## 1. Learning objective

**Concept.** Binary search for a partition point with no comparison against a target.
`flags` is a sequence of 0s followed by 1s, and the task is to return the index of the first
1, or `n` if there is none. This is lower-bound with the equality subtlety removed: the
predicate is given rather than computed.

**Why this problem (gap G1).** The family lacks a prerequisite. Learners who struggle with
lower-bound have nowhere simpler to go. The current bank also lacks a context where
boundary errors are observable with ≥ 2 behaviour groups outside lower-bound (CE1 gap 1).
This problem isolates the boundary and termination skills from equality handling.

**Interface.**

```cpp
int first_true(const std::vector<int>& flags);
```

`flags[i]` is 0 or 1, and the sequence is non-decreasing. `flags` may be empty, may be all
0s or may be all 1s. The function returns the smallest `i` with `flags[i] == 1`, or
`flags.size()` if there is none. Sizes go up to 200 000. The statement asks for O(log n).

**Subskills.** These are the existing skill keys. No new skill is needed (§2). Equality
handling is deliberately absent, since there is no target to compare.

| Key | What correct code must do here |
| --- | --- |
| `search_space_boundaries` | Keep every candidate answer in the range, from 0 through `n`, and never discard `flags[mid]` when it may be the answer. |
| `loop_termination` | Shrink the range every iteration and stop exactly when one candidate remains. |
| `problem_specification` | Return the *first* 1, or `n` when there is none. Never return -1, never "some 1", never the index before. |

**Prerequisites assumed.** Indexing a `std::vector`, `while` loops, integer division.

**Not assessed.** O(log n), since a linear scan gives identical output. Midpoint overflow
is also not assessed, since it is infeasible at these sizes.

## 2. Plausible implementation errors

| # | Error pattern | Model key | Skill | Predicted behaviour |
| --- | --- | --- | --- | --- |
| F1 | `hi = n - 1` with a half-open loop | `hi_init_last_index` | boundaries | Wrong only when the answer is `n` (no 1 present): `n - 1` |
| F2 | `hi = mid - 1` in a half-open loop, which discards `flags[mid]` | `hi_skips_candidate` | boundaries | Off by one below on many interior answers |
| F3 | `lo = 1` (1-based habit), so index 0 is never a candidate | `lo_init_one` | boundaries | Returns 1 when the answer is 0, and 1 on empty input |
| F4 | `lo = mid` instead of `mid + 1` | `no_progress_update` | termination | Time limit whenever the search moves right with two candidates left |
| F5 | Closed loop `lo <= hi` with `hi = n - 1` and `hi = mid` | `closed_loop_hi_mid` | termination | Time limit once `lo == hi` on a 1 |
| F6 | `while (hi - lo > 1)`: stops with two candidates left | `stops_one_early` | termination | Returns `lo` without checking it, so it is wrong when the answer is `lo + 1` |
| F7 | Returns -1 when there is no 1 (exact-search habit) | `none_sentinel` | specification | -1 instead of `n` |
| F8 | Returns `lo - 1` (last 0 instead of first 1) | `returns_last_false` | specification | Every answer one too small |
| F9 | Returns as soon as `flags[mid] == 1` | `returns_any_true` | specification | Some 1, not necessarily the first |
| F10 | Closed loop reading `flags[n]` | not modellable | boundaries | Undefined behaviour, which is the sanitizer's job |
| F11 | Linear scan | undetectable | none | Identical output |
| F12 | Two errors at once | not modelled | several | Should abstain as unmodelled |

**Skill taxonomy check.** Every modelled error is described by one of the three existing
keys, so no new skill is proposed.

F6 sits on the boundary between termination and boundaries. It is assigned to
`loop_termination` because it is a loop-condition error that does not match the interval
convention, which is the definition used in lower-bound. This is an assumption to be
revisited if measurement shows it is confused with a boundary model.

## 3. Test strategy

There are 19 tests: 2 samples and 17 hidden. The answer positions covered are 0, 1, an
interior position, `n − 1` and `n`. The sizes covered are 0, 1, 2, 3, small and 200 000.

- Tests with answer `n` (`sample_none`, `single_false`, `two_false`, `large_none`) are the
  only evidence for F1 and F7.
- Tests with answer 0 and empty input (`empty`, `all_true`, `single_true`, `two_true`,
  `large_all_true`) carry F3.
- Interior and `n − 1` answers (`two_false_true`, `three_middle`, `second_index`,
  `last_index`, `interior_odd`, `large_last`) carry F2 and F6.
- `ten_answer_three`, `large_interior` and `three_last` are the interior answers that F2 is
  predicted to *pass*. They split F2's evidence from the "fails every interior answer"
  models.

**Probes.** These are modelling assumptions:

| Probe | Skills |
| --- | --- |
| `empty_input` | boundaries |
| `answer_at_start` | boundaries |
| `answer_none` | boundaries, specification |
| `answer_last_index` | boundaries |
| `answer_interior` | specification |
| `single_element` | boundaries, termination |
| `two_elements` | termination |
| `large_input` | termination |

**Harness input.** `L n f_1 .. f_n` gives a literal array. `P n k` gives `k` zeros followed
by `n − k` ones.

## 4. Discrimination

### 4.1 Predicted (design time, Python re-implementation; not a measurement)

| Test | Reference | `hi_init_last_index` | `hi_skips_candidate` | `lo_init_one` | `no_progress_update` | `closed_loop_hi_mid` | `none_sentinel` | `returns_last_false` | `returns_any_true` | `stops_one_early` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `sample_interior` | 2 | · | 1 | · | TLE | TLE | · | 1 | · | · |
| `sample_none` | 3 | 2 | · | · | TLE | · | -1 | 2 | · | 2 |
| `empty` | 0 | · | · | 1 | · | · | -1 | -1 | · | · |
| `all_true` | 0 | · | · | 1 | · | TLE | · | -1 | 2 | · |
| `single_true` | 0 | · | · | 1 | · | TLE | · | -1 | · | · |
| `single_false` | 1 | 0 | · | · | TLE | · | -1 | 0 | · | 0 |
| `two_false_true` | 1 | · | 0 | · | TLE | TLE | · | 0 | · | 0 |
| `two_true` | 0 | · | · | 1 | · | TLE | · | -1 | 1 | · |
| `two_false` | 2 | 1 | · | · | TLE | · | -1 | 1 | · | · |
| `three_last` | 2 | · | · | · | TLE | TLE | · | 1 | · | · |
| `three_middle` | 1 | · | 0 | · | TLE | TLE | · | 0 | · | 0 |
| `second_index` | 1 | · | 0 | · | TLE | TLE | · | 0 | 3 | 0 |
| `last_index` | 4 | · | 3 | · | TLE | TLE | · | 3 | · | 3 |
| `interior_odd` | 3 | · | 2 | · | TLE | TLE | · | 2 | · | 2 |
| `ten_answer_three` | 3 | · | · | · | TLE | TLE | · | 2 | 5 | · |
| `large_interior` | 123457 | · | · | · | TLE | TLE | · | 123456 | 150000 | · |
| `large_none` | 200000 | 199999 | · | · | TLE | · | -1 | 199999 | · | · |
| `large_all_true` | 0 | · | · | 1 | · | TLE | · | -1 | 100000 | · |
| `large_last` | 199999 | · | 199998 | · | TLE | TLE | · | 199998 | · | 199998 |

**Predicted support.**

| Model | Tests | Behaviour groups |
| --- | --- | --- |
| `hi_init_last_index` | 4 | 2 |
| `hi_skips_candidate` | 7 | 3 |
| `lo_init_one` | 5 | 3 |
| `no_progress_update` | 14 | 7 |
| `closed_loop_hi_mid` | 14 | 7 |
| `none_sentinel` | 5 | 3 |
| `returns_last_false` | 19 | 10 |
| `returns_any_true` | 6 | 3 |
| `stops_one_early` | 8 | 3 |

The weakest pair is `hi_skips_candidate` / `stops_one_early`, separated by 3 tests.

### 4.2 Measured (2026-10-18, content `b69c5efa3b39`, g++ 14.2.0 under runc)

The live matrix is in [../content-reports/first-true.md](../content-reports/first-true.md).
Validation passes with 0 errors, 0 warnings and 1 documented limitation (`hi_init_last_index`).

**Where the prediction was wrong.** The prediction was wrong for `stops_one_early` on 6
tests: `sample_interior`, `two_false`, `three_last`, `ten_answer_three`, `large_interior`
and `large_none`. The C++ model, written to the description in §2, returns `lo` unchecked
and so also fails every answer-`n` test and every interior answer at `lo + 1`. The Python
re-implementation used at design time did not. The six `distinguishes` declarations were
corrected to the measurement. Every other cell matched the prediction.

| Model | Tests | Behaviour groups (measured) | Predicted groups |
| --- | --- | --- | --- |
| `hi_init_last_index` | 4 | **1** (documented limitation) | 2 |
| `hi_skips_candidate` | 7 | **2** | 3 |
| `lo_init_one` | 5 | **3** | 3 |
| `no_progress_update` | 14 | 5 | 7 |
| `closed_loop_hi_mid` | 14 | 6 | 7 |
| `stops_one_early` | 14 | 5 | 3 |
| `none_sentinel` | 5 | 2 | 3 |
| `returns_last_false` | 19 | 8 | 10 |
| `returns_any_true` | 6 | 3 | 3 |

There are 8 behaviour groups in all.
- The weakest pair is `returns_last_false` / `stops_one_early`: 5 distinguishing tests.
- Next is `hi_skips_candidate` / `stops_one_early`: 7.
- No pair is inseparable.

`no_progress_update` and `stops_one_early` fail the same 14 tests. They are separated by
signature, a time limit versus a wrong output, not by which tests fail.

**CE1.1 boundary target: met.** Two boundary models have at least 2 measured groups:
`hi_skips_candidate` (2) and `lo_init_one` (3). `hi_init_last_index` lost its predicted
second group, because `stops_one_early` now fails the same answer-`n` tests. It stays a
qualified, documented collision, as planned.

**F6 against the boundary models.** `stops_one_early` is not confused with any boundary
model: it differs from `hi_skips_candidate` on 7 tests and from `hi_init_last_index` on 10.
Its `loop_termination` assignment stands.

**Held-out (v1.1).**
- 2 of 3 modelled cases diagnosed correctly: `hi_skips_candidate` and `lo_init_one`.
- `returns_any_true` abstained (false negative).
- Both unmodelled cases abstained.
- Both correct cases passed.
- 7 of 7 reproducible.
- Details: [../evaluation/ce1.1-2026-10-18/](../evaluation/ce1.1-2026-10-18/README.md).

### 4.3 Ambiguity analysis (before measurement)

- **F1.** Every test that detects F1 has answer `n`. Any unmodelled "cannot return `n`"
  error (for example clamping to `n − 1`) produces the same failures. Its predicted second
  group exists only because F6 splits the answer-`n` tests; it does not remove the
  collision.
  - F1 keeps a documented `known_limitation`.
  - Its diagnoses are therefore qualified and are not skill evidence (ledger policy 1.2).
  - The CE1.1 boundary target therefore rests on F2 and F3, not F1.
- **F3.**
  - **Collision risk:** an unmodelled "returns 1 for an empty array" error would match only
    on `empty`. The two-group requirement guards against this.
  - **Behaviour groups:** F3's second group comes from F7 and F8 distinguishing `empty`
    from the answer-0 tests.
- **F2 and F6** both fail some interior answers. The prediction separates them on 3
  tests. If measurement shows them inseparable, the diagnosis must report them as
  ambiguous, not pick one.
- **F4 and F5** are seen only as time limits (CPU-limit stops, ADR-023 D1). A time limit
  is the least specific signature, so slow unmodelled code can mimic them.

## 5. From evidence to concepts

| Observed | Hypothesis | Skill | Next activity (the record's intent; policy v1 does not act on it) |
| --- | --- | --- | --- |
| Off by one below on interior answers | F2 | boundaries | lower-bound, where `hi_skips_candidate` is also modelled |
| 1 when the answer is 0 or the array is empty | F3 | boundaries | lower-bound |
| Wrong only when there is no 1 | F1 (qualified) or F7 | boundaries / specification | lower-bound's `above_all` tests |
| Time limits | F4 or F5 | termination | G2 (integer square root) once it exists |
| Some 1 but not the first | F9 | specification | lower-bound (`duplicates_*` tests) |
| Abstention | unmodelled | none claimed | retry; flagged for review |

## 6. Follow-up and curriculum links

- **Role.** First-true is the prerequisite of the binary-search family.
- **`[curriculum]` links.** It has no prerequisite in the bank.
  - Its `assumes` list names array indexing and loops.
  - It lists no equivalents.
  - The reverse link (lower-bound `prerequisites = ["first-true"]`) is **not added**. It
    would change lower-bound's content version, which CE1 preserves. It is deferred to a
    reviewed content change.
- **Recommendation behaviour (decision E2).** `recommendable = false`.
  - Policy v1 never recommends first-true.
  - The problem stays in the problem list.
  - Its attempts are diagnosed, enter skill evidence and the researcher-only learner
    model, and get a v1 recommendation among the recommendable problems, as any attempt
    does.
  - A history that contains no first-true attempt produces exactly the same
    recommendations as before. A regression test checks this.
- **Follow-up criterion.** This is the family rule: every reliable follow-up test probing
  the diagnosed skill passes, and no model of that skill is diagnosed.

## 7. Held-out plan and known limitations

**Held-out plan.** There will be 7 cases:
- 2 correct, in different styles;
- 3 modelled, for F2, F3 and F9, in a style different from the models;
- 2 unmodelled: a double error, and an empty-array special case returning -1.

They are written and committed after the content and before `codeadapt-eval` runs on them.
They live in `eval/heldout/first-true/`. No calibration cases are planned. If any are
written, they go in `eval/calibration/first-true/` and are reported separately.

**Measured limitation: F9's midpoint dependence.** The held-out case
`classic_found_return.cpp` is a closed-interval search that returns the first 1 it lands
on. It abstained because "some 1" depends on the midpoint convention, and the model covers
only the half-open one.

**Owner decision (2026-10-21): accepted as a documented limitation.** C7, a
closed-interval variant of F9, is not authorised. `returns_any_true` therefore covers one
midpoint convention only. Variants with other midpoints abstain, which is safe: no wrong
diagnosis is shown. Nothing in this record claims that other midpoint conventions are
covered.

**Known limitations, before measurement.**
- F1 collides by design.
- F4 and F5 are visible only as time limits.
- The O(log n) requirement is not assessed.
- The held-out cases are written by the models' author.
- The F2 versus F6 separation rests on a few small tests.
