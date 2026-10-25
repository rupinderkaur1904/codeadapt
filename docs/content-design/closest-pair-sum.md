# Content design record: `closest-pair-sum` (bank expansion batch A2, 2026-10-25)

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) and the
[content report](../content-reports/closest-pair-sum.md).

## 1. Learning objective and contract

The opposite-ends two-pointer technique on a sorted array. This is the entry problem of the
`two-pointers` family.

```cpp
int closest_pair_gap(const std::vector<int>& a, int target);
```

- Return `min |a[i] + a[j] - target|` over `i < j`.
- `2 <= n <= 100000` and `|a_i|, |target| <= 10^8`, so every sum and difference fits in an
  `int`.

## 2. Error models

| Model | Skill | Error | Detecting tests / groups |
| --- | --- | --- | --- |
| `allows_same_element` | index_range | `lo <= hi`, so an element can pair with itself | 6 / 4 |
| `moves_wrong_pointer` | update_rule | Moves `hi` when the sum is too small | 10 / 5 |
| `skips_first` | index_range | `lo` starts at 1 | 4 / 4 |
| `signed_gap` | output_contract | Returns `sum - target` with its sign | 6 / 4 |

## 3. Tests

There are 13 tests:

- 2 samples;
- self-pair traps, including a two-element one;
- the first element needed;
- exactly two elements;
- every sum above the target, and every sum below it;
- negative values;
- duplicates;
- a case where the direction matters;
- two large arithmetic sequences, one with an exact pair.

## 4. Attribution checks

- **A double loop with `j` starting at `i`** is identical to `allows_same_element` on every
  random input. Both are index-range errors, so the skill attribution is unique.
- **Checking only neighbouring pairs, or returning the closest sum**, differs from every model.
  These are unmodelled, and they are used as held-out cases.

## 5. Role and held-out plan

- `recommendable = false`; family `two-pointers`.
- There are 8 held-out cases:
  - 2 correct (64-bit two pointers; a binary search for each partner);
  - 4 modelled;
  - 2 unmodelled.
