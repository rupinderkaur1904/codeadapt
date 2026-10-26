# Content design record: `exact-search` (BSX, binary-search extension)

> **Update 2026-10-26.** New content version `94bfc112e9e7…` (was `9cdc3cfe5d92…`). The record below describes the problem as designed and is unchanged.
>
> **L20 safeguard S1 (ADR-036).** `swapped_direction`, `lo_init_one` now carry a `known_limitation` (a cross-skill twin, docs/reviews/2026-10-25/l20-search.md); diagnoses are qualified and add no negative evidence.
>
> **Banned names (ADR-035).** `banned_names` lists `std::binary_search`, `std::equal_range`, `std::find`, `std::lower_bound`, `std::partition_point`, `std::upper_bound`; an attempt that names one gives no skill observations.
>
> **Positive-only skills (ADR-034).** `search_space_boundaries` has no model that can give negative evidence; the reason is recorded under `positive_only_skills`.

**Label.** Files and commits call this "CE2". That was a working label; this is a binary-search family extension, not the planned CE2 stage (arrays).

**Status and order.** This record follows the same order as [upper-bound](upper-bound.md):

1. Written on 2026-10-24 together with the content.
2. The matrix was predicted by native runs.
3. The matrix was measured in the sandbox. The measurement is authoritative:
   [content report](../content-reports/exact-search.md).
4. The held-out cases were committed after the content and before evaluation.

## 1. Learning objective

The classic search: find a target's index in a strictly increasing array, or report that it is
absent. It is the first problem in the bank where the search can stop early on equality, and
where "absent" has its own return value (-1) rather than a boundary index.

**Contract.**

```cpp
int search_index(const std::vector<int>& a, int target);
```

- `a` is strictly increasing and may be empty. The harness rejects repeated values with exit 64,
  which is never reached by the suite.
- Return the index of `target`, or -1.

**Skills.** `search_space_boundaries`, `loop_termination` and `problem_specification`.

- `equality_handling` is not used. With distinct values there is no "which side do equal
  elements go" question.
- No new skill is proposed.

**Not a duplicate.**

- lower-bound returns a boundary index even when the target is absent. Here an absent target
  must give -1.
- first-true searches 0/1 flags.

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `closed_loop_lt` | loop_termination | Closed range, but the loop runs while `lo < hi`, so the last candidate is never compared (returns -1) |
| `no_progress_update` | loop_termination | `lo = mid`, so there is no progress (time limit) |
| `swapped_direction` | search_space_boundaries | Moves the wrong bound, so the target is found only when a midpoint hits it |
| `lo_init_one` | search_space_boundaries | `lo = 1`, so index 0 is unreachable |
| `returns_insertion_point` | problem_specification | Returns `lo` instead of -1 when the target is absent |
| `returns_value` | problem_specification | Returns `a[mid]` instead of `mid` |

**Not modelled.**

- A 1-based index.
- Two errors at once.
- `hi = n` in a closed range. That reads past the end, which the sanitizer reports as
  unreliable evidence; it is never diagnosed.

## 3. Tests

There are 19 tests:

- 2 samples (present and absent);
- empty;
- the target first, last, second, fourth, below all, above all, or absent in between;
- single elements and pairs;
- negative values, where the index differs from the value;
- four large tests (200,000 elements).

## 4. Known risks

- `closed_loop_lt`, `lo_init_one` and `swapped_direction` all fail by returning -1, but on
  different sets of tests. A program that always returns -1 is consistent with none of them,
  because each passes some present-target test. Such a program abstains.
- `no_progress_update` is seen only as time limits. Under v1.3 it is never named.
- O(log n) is not assessed.

## 5. Role and held-out plan

- `recommendable = false` (E2); policy unchanged.
- There are 7 held-out cases:
  - 2 correct (recursive; lower bound plus a check);
  - 3 modelled (`closed_loop_lt`, `returns_insertion_point`, `lo_init_one`);
  - 2 unmodelled (a 1-based index; `lo = 1` plus the insertion point).
