# Content design record: `dedup-sorted` (bank expansion batch A2, 2026-10-25)

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) and the
[content report](../content-reports/dedup-sorted.md).

## 1. Learning objective and contract

The same-direction read/write two-pointer technique.

```cpp
int remove_duplicates(std::vector<int>& a);
```

- The array is sorted. Compact the distinct values in place and return their count `k`.
- The harness prints `k` and the first `k` elements. Above 40 values it prints a hash instead.
  A `k` outside `[0, n]` is printed as invalid, never read out of range.

**Replacing an earlier choice.** This problem replaces the planned `squares-sorted`. Its likely
errors collided with one another:

- comparing raw values instead of absolute values gives exactly the output of not sorting at
  all;
- filling from the front gives exactly the output of sorting in descending order.

So its diagnoses would mostly be ambiguous or non-unique.

## 2. Error models

| Model | Skill | Error | Detecting tests / groups |
| --- | --- | --- | --- |
| `returns_last_index` | output_contract | Returns one less than the count, with the prefix one element short. **Documented limitation: attribution not unique (L20)** | 12 / 6 |
| `skips_last` | index_range | Read loop stops one element early | 7 / 3 |
| `compares_to_first` | update_rule | Compares with `a[0]` instead of the last kept value | 5 / 3 |
| `counts_without_writing` | update_rule | Counts correctly but never moves the values | 5 / 3 |

**Why `returns_last_index` carries a `known_limitation`.** "Keep a value when it differs from
the next one", with the final element forgotten, is a loop-range error. On every valid input it
produces the same `k - 1` and the same short prefix. The attribution to `output_contract` is
therefore not unique (ADR-032 route).

## 3. Tests

There are 12 tests:

- 2 samples;
- every value equal;
- a single element;
- a two-element case with a new last value;
- duplicates only at the start, and only at the end;
- negatives;
- duplicates of the first value only;
- every value twice;
- two large block patterns.

## 4. Role and held-out plan

- `recommendable = false`; family `two-pointers`.
- There are 8 held-out cases:
  - 2 correct;
  - 4 modelled;
  - 2 unmodelled.
