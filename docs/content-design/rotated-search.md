# Content design record: `rotated-search` (BSX, binary-search extension)

> **Update 2026-10-26.** New content version `14e8af1098ad…` (was `8568f135e8ad…`). The record below describes the problem as designed and is unchanged.
>
> **L20 safeguard S1 (ADR-036).** `left_range_excludes_lo` now carries a `known_limitation` (a cross-skill twin, docs/reviews/2026-10-25/l20-search.md); diagnoses are qualified and add no negative evidence.
>
> **Banned names (ADR-035).** `banned_names` lists `std::binary_search`, `std::find`, `std::lower_bound`, `std::partition_point`, `std::upper_bound`; an attempt that names one gives no skill observations.
>
> **Positive-only skills (ADR-034).** `equality_handling` has no model that can give negative evidence; the reason is recorded under `positive_only_skills`.

**Label.** Files and commits call this "CE2". That was a working label; this is a binary-search family extension, not the planned CE2 stage (arrays).

**Status and order.** This record was written on 2026-10-24 together with the content, during
the overnight bank expansion.

- **Predicted, then measured.** Native runs (a scratch tool, not committed) predicted the
  matrix. It was then measured in the sandbox, and the measurement is authoritative: see the
  [content report](../content-reports/rotated-search.md).
- **Held-out cases.** They were committed after the content and before `codeadapt-eval` ran on
  them.

## 1. Learning objective

Search a rotated sorted array for a target. The core idea is that, around `mid`, one of the
two halves `[lo, mid]` and `[mid, hi]` is always sorted. The search continues in that half only
if it can hold the target.

This problem combines `exact-search` (closed interval, early return on a match) with
`rotated-min` (reasoning about where the rotation lies).

**Contract.**

```cpp
int rotated_search(const std::vector<int>& a, int target);
```

- `a` is a rotation of a strictly increasing array. It may not be rotated at all.
- `1 <= n <= 200000`.
- The harness checks the rotation property, the distinct values and the size.
- The function returns the index of `target`, or -1 if `target` is absent.
- The statement asks for O(log n) and forbids the library searches. Neither rule is enforced
  (see §4).

**Skills.** The problem uses three of the four existing keys.

- **Not listed: `search_space_boundaries`.** No plausible bound-initialisation error was found
  that differs from the ones already in `exact-search`. That gap is noted here, not filled with
  an implausible model.
- **No new skill.** None is proposed.
- **Skill mappings.** Each model's mapping to a skill is a modelling assumption.

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `left_half_test_strict` | equality_handling | Uses `a[lo] < a[mid]` as the "left half sorted" test, which is wrong when `lo == mid` |
| `left_range_excludes_lo` | equality_handling | Uses `a[lo] < target` for the left half, so a target equal to `a[lo]` is searched for in the wrong half |
| `closed_loop_lt` | loop_termination | Loops `while (lo < hi)`, so the last candidate is never compared and -1 is returned |
| `ignores_rotation` | problem_specification | Runs an ordinary binary search, as if `a` were not rotated |
| `returns_sorted_position` | problem_specification | Returns the position in sorted order instead of the index in `a` |

`closed_loop_lt` gives a **visible, terminating** wrong output (-1), not a time limit. This
helps with gap G2 from the CE1 proposal: until now, termination errors were seen only as time
limits.

**Not modelled.**

- **The symmetric `target <= a[hi]` error.** This is the right-half version of
  `left_range_excludes_lo`. It is left out to avoid two near-identical models.
- **A linear scan.** It is correct and passes the tests.
- **Two errors at once.**

## 3. Tests

There are 21 tests:

- 2 sample tests;
- targets in the left run (first and middle), in the right run (first and last), and absent;
- arrays that are not rotated, with the target first or last;
- single-element arrays, with the target present or absent;
- rotated and sorted pairs;
- arrays of three, four and seven elements, chosen so the search ends on specific ranges;
- four large tests (200,000 elements).

## 4. Measured discrimination and ambiguity

The sandbox validation result is `ok`, with one documented limitation. The measured matrix
equals the native prediction.

**`left_half_test_strict` is single-group.**

- It is detected by 2 tests (`two_rotated_second` and `four_min_last`), which form one
  behaviour group.
- A brute-force search over every rotation and every present target for `n = 3..9` found only
  this one failing pattern. The error shows only when the search ends on a rotated pair whose
  second element is the target.
- On those tests its output (-1) equals the output of `closed_loop_lt` and of
  `ignores_rotation`. It separates from them because it passes their other failing tests.
- It carries a `known_limitation`, and its diagnoses are reported as qualified.

**Five tests detect no model.** Absent targets and `large_sorted_hit` detect none. They stay in
the suite as correctness checks.

**O(log n) is not assessed.** A linear scan passes.

## 5. Role in the bank and recommendation

- **Not recommendable.** The problem has `recommendable = false` (decision E2). Policy 1.4 and
  its golden test are unchanged.
- **Evidence.** Attempts are diagnosed and produce skill evidence for the researcher-only
  learner model.
- **Prerequisites.** `prerequisites = ["exact-search", "rotated-min"]`.

## 6. Held-out plan

There are 8 cases in `eval/heldout/rotated-search/`, all written by the models' author:

- 2 correct;
- 4 modelled, written in different styles;
- 2 unmodelled.
