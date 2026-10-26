# Content design record: `distinct-in-windows` (bank expansion batch A3, 2026-10-25)

> **Update 2026-10-26.** New content version `7948c0fabbdf…` (was `e3bcaf715296…`). The record below describes the problem as designed and is unchanged.
>
> **Skill keys (ADR-034).** `keeps_zero_counts` → `window_maintenance`; `misses_last_window` → `loop_bounds`. Declared skills are now `tie_resolution`, `loop_bounds`, `window_maintenance`.

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) and the
[content report](../content-reports/distinct-in-windows.md), which is authoritative.

## 1. Learning objective and contract

Maintain a frequency table over a sliding window, including removing values whose count drops
to zero.

```cpp
std::vector<int> distinct_in_windows(const std::vector<int>& a, int k);
```

- `1 <= k <= a.size() <= 10^5`, `0 <= a[i] <= 10^9`; O(n) expected or O(n log n).
- The result is printed in full when it has at most 40 entries, otherwise as length, first,
  last and a fixed polynomial hash.

## 2. Error models

| Model | Skill | Error | Detecting tests / groups |
| --- | --- | --- | --- |
| `keeps_zero_counts` | update_rule | Decrements the leaving value but never erases it at zero | 6 / 2 |
| `misses_last_window` | index_range | The loop stops one element early | 12 / 4 |
| `counts_unique_only` | tie_resolution | Counts values that occur exactly once | 7 / 2 |

**Dropped during design.** `never_removes` (never decrementing at all) is output-identical to
`keeps_zero_counts`, so it was deleted; the remaining model's description names both routes and
a set that only grows.

## 3. Tests

There are 12 tests: 2 samples, all distinct, a value that returns, a value that leaves for good,
`k = n`, `k = 1`, pairs in a window, a new value at the end, a single element, and two generated
arrays of 100000 (a short cycle and all distinct).

## 4. Attribution checks (400 random inputs)

- **A `std::set` that only grows** is identical to `keeps_zero_counts`. Same skill
  (`update_rule`), so the attribution stays; the model description says so.
- **Erasing the leaving value even when it still occurs** is unmodelled.
- **Rebuilding a set for each window** is correct on every random input but O(nk).

## 5. Role and held-out plan

- `recommendable = false`; family `sliding-window`.
- 7 held-out cases: 2 correct, 3 modelled, 2 unmodelled.
