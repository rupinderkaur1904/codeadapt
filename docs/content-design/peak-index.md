# Content design record: `peak-index` (CE2)

**Status and order.**

- Written on 2026-10-24 together with the content, during the overnight bank expansion.
- The matrix was predicted by native runs (a scratch tool, not committed), then measured in the
  sandbox. The measurement is authoritative: [content report](../content-reports/peak-index.md).
- The held-out cases were committed after the content and before `codeadapt-eval` ran on them.

## 1. Learning objective

Binary search driven by a **local** comparison, `a[mid]` against `a[mid + 1]`, with no target
and no fixed reference element. The rising prefix of a mountain array is the predicate's true
part, and the answer is the first index where it fails.

**Contract.**

```cpp
int peak_index(const std::vector<int>& a);
```

- `a` strictly increases, then strictly decreases. Either part may be empty.
- `1 <= n <= 200000`, checked by the harness.
- Return the index of the largest element.
- Asks for O(log n) and forbids `std::max_element`. Neither rule is enforced (§4).

**Skills.** Three of the four existing keys. `equality_handling` is not listed: adjacent
elements are never equal, so `<` and `<=` behave identically. No new skill is proposed.

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `swapped_direction` | search_space_boundaries | A rising step at `mid` discards the right half, which holds the peak |
| `hi_skips_candidate` | search_space_boundaries | `hi = mid - 1` on a falling step, which discards `mid` |
| `no_progress_update` | loop_termination | `lo = mid`, so the range stops shrinking (time limit) |
| `stops_one_early` | loop_termination | Loops `while (hi - lo > 1)` and returns `lo` without comparing the last two |
| `returns_value` | problem_specification | Returns `a[lo]` instead of `lo` |

`stops_one_early` is a terminating loop error that is **visible in the output**, as in
rotated-search (gap G2).

**Not modelled.**

- Comparing with `a[mid - 1]`. It reads out of bounds at `mid = 0`, so it would produce
  `unreliable_evidence`, not a fingerprint.
- A linear scan. It is correct and passes.
- Two errors at once.

## 3. Tests

There are 16 tests:

- 2 samples: an inside peak, and an increasing-only array;
- a single element, and both two-element shapes;
- a decreasing-only array;
- peaks second and second-to-last;
- small arrays of 3 and 4, a long descent, and negative values;
- four large tests (200,000 elements) with the peak first, last, inside, and second-to-last.

## 4. Measured discrimination and ambiguity

Sandbox validation result: `ok`, with **no warnings**. Every model is detected in at least 2
behaviour groups. The measured matrix equals the native prediction.

- **`hi_skips_candidate` and `stops_one_early` overlap on four tests.** On those tests they give
  the same outputs (for example, both return `peak - 1`).
  - They separate on four other tests. `sample_middle` and `negatives` fail only for
    `hi_skips_candidate`; `two_up` and `peak_second` fail only for `stops_one_early`.
- **`returns_value` passes `large_peak_first` by coincidence.** There the value at index 0 is 0.
  It fails 15 other tests.
- **`no_progress_update` is seen only as time limits.** It is never named under v1.3.
- **O(log n) is not assessed.** A linear scan passes.

## 5. Role in the bank and recommendation

- `recommendable = false` (decision E2). Policy 1.4 and its golden test are unchanged.
- Attempts are diagnosed and produce skill evidence for the researcher-only learner model.
- `prerequisites = ["first-true", "rotated-min"]`.

## 6. Held-out plan

There are 8 cases in `eval/heldout/peak-index/`, all written by the models' author:

- 2 correct;
- 4 modelled in different styles;
- 2 unmodelled.
