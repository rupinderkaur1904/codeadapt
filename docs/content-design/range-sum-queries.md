# Content design record: `range-sum-queries` (bank expansion batch A4, 2026-10-25)

> **Update 2026-10-26.** New content version `74d198449c3a…` (was `d47598c44246…`). The record below describes the problem as designed and is unchanged.
>
> **Skill keys (ADR-034).** `excludes_right_end` → `range_inclusion`; `prefix_not_accumulated` → `running_state`. Declared skills are now `output_contract`, `range_inclusion`, `running_state`.

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) and the
[content report](../content-reports/range-sum-queries.md), which is authoritative.

## 1. Learning objective and contract

Build a prefix-sum array once and answer each inclusive range query with one subtraction.

```cpp
std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries);
```

- `1 <= a.size(), queries.size() <= 10^5`, `-10^4 <= a[i] <= 10^4`, `0 <= l <= r < n`; O(n + q).
- Mode `G` generates queries from a seed, so large tests stay small on disk. Long results are
  printed as length, first, last and a fixed polynomial hash.

## 2. Error models

| Model | Skill | Error | Detecting tests / groups |
| --- | --- | --- | --- |
| `excludes_right_end` | index_range | `prefix[r] - prefix[l]`, so `a[r]` is left out | 9 / 3 |
| `prefix_not_accumulated` | update_rule | Stores each element instead of the running total | 9 / 3 |
| `ignores_left_end` | output_contract | Returns `prefix[r + 1]`, the sum from the start | 7 / 2 |

## 3. Tests

There are 10 tests: 2 samples, single-element ranges, ranges from the start, middle ranges, a
range ending at index 0, negatives, a one-element array, repeated queries, and a generated
test with 100000 elements and 100000 queries.

## 4. Attribution checks (400 random inputs)

- **A direct loop `i < r`** is identical to `excludes_right_end`. Same skill (`index_range`).
- **An inclusive prefix used as `prefix[r] - prefix[l]`** (drops `a[l]`) is unmodelled; it
  agrees with `excludes_right_end` on 153 of 400 inputs.

## 5. Role and held-out plan

- `recommendable = false`; family `prefix-sums`.
- 7 held-out cases: 2 correct, 3 modelled, 2 unmodelled.
