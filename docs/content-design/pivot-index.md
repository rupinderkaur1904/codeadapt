# Content design record: `pivot-index` (bank expansion batch A4, 2026-10-25)

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) and the
[content report](../content-reports/pivot-index.md), which is authoritative.

## 1. Learning objective and contract

Use a total and a running prefix sum to compare the two sides of each index in O(n).

```cpp
int pivot_index(const std::vector<int>& a);
```

- `1 <= a.size() <= 10^5`, `-10^4 <= a[i] <= 10^4`. Return the **first** index whose strict left
  and right sums are equal, or `-1`.

## 2. Error models

| Model | Skill | Error | Detecting tests / groups |
| --- | --- | --- | --- |
| `pivot_counted_left` | update_rule | Adds `a[i]` to the left sum before comparing | 11 / 3 |
| `pivot_counted_right` | update_rule | Right sum is `total - left`, so the pivot counts on the right | 10 / 2 |
| `last_pivot` | tie_resolution | Returns the last balancing index | 3 / 2 |
| `size_when_none` | output_contract | Returns `n` instead of `-1` when nothing balances | 5 / 2 |

## 3. Tests

There are 15 tests: 2 samples, pivot first and last, all zeros, two pivots (twice, one added to
separate `last_pivot`), a single element, a case where the pivot's own value matters, left- and
right-heavy traps, a negative total, and three generated arrays (symmetric, zeros, none).

## 4. Attribution checks (400 random inputs)

- **Scanning from the right and returning the first balance found** is identical to
  `last_pivot`. Same skill (`tie_resolution`), so the attribution stays.
- **Skipping the first and last index** and **returning 0 when none** are unmodelled. The second
  agrees with `size_when_none` on 189 of 400 inputs but differs on the others.

## 5. Role and held-out plan

- `recommendable = false`; family `prefix-sums`.
- 8 held-out cases: 2 correct, 4 modelled, 2 unmodelled.
