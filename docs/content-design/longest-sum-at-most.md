# Content design record: `longest-sum-at-most` (bank expansion batch A3, 2026-10-25)

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) and the
[content report](../content-reports/longest-sum-at-most.md), which is authoritative.

## 1. Learning objective and contract

A variable-size window: grow on the right, shrink from the left while the sum is over the
limit, and measure the window correctly.

```cpp
int longest_at_most(const std::vector<int>& a, int s);
```

- `1 <= a.size() <= 10^5`, `1 <= a[i] <= 10^4`, `1 <= s <= 10^9`. Return the length of the
  longest contiguous window whose sum is at most `s` (0 if none).

## 2. Error models

| Model | Skill | Error | Detecting tests / groups |
| --- | --- | --- | --- |
| `length_without_plus_one` | index_range | Measures the window as `right - left` | 13 / 4 |
| `strict_limit` | output_contract | Treats "at most s" as "less than s" | 6 / 2 |
| `restarts_window` | update_rule | When over the limit, restarts at the current element instead of shrinking | 4 / 2 |

## 3. Tests

There are 14 tests: 2 samples (one where the sum hits `s` exactly), a big element then small
ones, many elements to drop, three tests added during design to separate `restarts_window`
(`keep_tail`, `drop_one_keep_rest`, `exact_after_overlap`), the whole array, nothing fits, one
element fits, a single exact element, a loose budget, and two generated arrays of 100000.

## 4. Attribution checks (400 random inputs)

- **Shrinking with `if` instead of `while` is correct** for the maximum length when values are
  positive: the window never shrinks below the best length found so far. It was first drafted
  as an error model and moved to `alternatives/shrinks_once_correct.cpp`; it passes every test
  and every random input.
- **Using `s - 1` as the limit** is identical to `strict_limit` on every input. Both are a
  misreading of the limit in the specification, so the attribution to `output_contract` stays.
- **Recording the length before shrinking** and **only windows starting at 0** are unmodelled.

## 5. Role and held-out plan

- `recommendable = false`; family `sliding-window`.
- 7 held-out cases: 2 correct, 3 modelled, 2 unmodelled.
