# Content design record: `last-occurrence` (CE2)

**Status and order.**

- Written on 2026-10-24 together with the content, during the owner-requested overnight bank
  expansion, as for `upper-bound`.
- The matrix was predicted by native runs (a scratch tool, not committed), then measured in the
  sandbox. The measurement is authoritative: [content report](../content-reports/last-occurrence.md).
- The held-out cases were committed after the content and before `codeadapt-eval` ran on them.

## 1. Learning objective

Find the index of the last occurrence of a target in a sorted array with duplicates, or -1. The
task combines an upper-bound search with a check of the element just before the boundary.

**Contract.**

```cpp
int last_occurrence(const std::vector<int>& a, int target);
```

- `a` is non-decreasing and may be empty or contain repeats.
- Return the largest `i` with `a[i] == target`, or -1 if the target does not occur.
- Asks for O(log n) and forbids the library searches. Neither rule is enforced (§4).

**Skills.** The four existing keys; no new skill is proposed.

**How it differs from the existing problems.**

- `exact-search` uses strictly increasing input, so any match is the answer. Here duplicates
  make "which occurrence" the point.
- `lower-bound` and `upper-bound` return a boundary, including `a.size()`. Here the answer is an
  element index or -1.
- `last-less-than` returns the last element strictly below the target. Here the element must
  equal the target.

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `returns_first_occurrence` | equality_handling | Lower bound plus a check, so it returns the first occurrence |
| `stops_at_any_match` | equality_handling | Closed search that returns on `a[mid] == target`, so it returns some occurrence |
| `hi_init_last_index` | search_space_boundaries | `hi = n - 1` with a half-open loop, so index `n - 1` is never confirmed |
| `no_progress_update` | loop_termination | `lo = mid`, so the range stops shrinking (time limit) |
| `missing_equality_check` | problem_specification | Returns `lo - 1` unchecked: the last element `<= target`, even when absent |
| `returns_one_past` | problem_specification | Returns the upper bound (one past the last occurrence) when present |

**Not modelled.**

- Two errors at once.
- Scanning left or right from a match. This is correct but O(n), and it passes.
- Linear scans and `std::upper_bound`. These are correct.

## 3. Tests

There are 19 tests:

- 2 samples: a run of duplicates, and an absent target;
- empty, below all, above all, and absent just after a run;
- unique targets in the middle and at the end;
- runs at the start, at the end and in the middle, and all equal;
- single elements and pairs;
- three large tests (200,000 elements).

Probes and skills follow lower-bound's mapping (a modelling assumption).

## 4. Measured discrimination and ambiguity

See the content report.

**Known risks (predicted natively; the report is authoritative).**

- **The two equality models overlap.**
  - `stops_at_any_match` fails only duplicate tests.
  - `returns_first_occurrence` fails those tests too, plus `run_at_start`.
  - On shared tests their outputs differ (for example 2 against 1 on `sample_run`), so they
    separate on observed output, not only on which tests fail.
- **`stops_at_any_match`'s output depends on midpoint convention.** A program using
  `(lo + hi + 1) / 2` returns a different occurrence. Such a program would show unmodelled
  output and should lead to abstention, not a name (the first-true limitation).
- **`hi_init_last_index` and `stops_at_any_match` collide on one test.** Both output 4 on
  `run_at_end`. They differ elsewhere: `unique_last` and `single_equal` fail only for
  `hi_init_last_index`.
- **`no_progress_update` is seen only as time limits.** Under v1.3 it is never named
  (ADR-027).
- O(log n) is not assessed, and a linear scan passes.

## 5. Role in the bank and recommendation

- `recommendable = false` (decision E2, applied to every new problem). Policy 1.4 and its golden
  test are unchanged.
- Attempts are diagnosed and produce skill evidence for the researcher-only learner model.
- `prerequisites = ["lower-bound", "count-occurrences"]`.

## 6. Held-out plan

There are 7 cases in `eval/heldout/last-occurrence/`, all written by the models' author:

- 2 correct;
- 3 modelled in different styles;
- 2 unmodelled.

## 7. Measured result (sandbox, 2026-10-24)

`codeadapt-content validate` result: `ok`. The measured matrix equals the native prediction.

- Every pair of models is separated by at least 6 tests.
- **Limitation.** `missing_equality_check` is detected by 5 tests that form one behaviour group,
  the absent-target tests. It carries a `known_limitation` and its diagnoses are reported as
  qualified.
- This matches the single-group `hi_init_last_index` limitation in the original four problems.
