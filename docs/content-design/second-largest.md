# Content design record: `second-largest` (bank expansion batch A1, 2026-10-25)

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) for the process and the skill
keys, and the [content report](../content-reports/second-largest.md) for the measurement.

## 1. Learning objective and contract

Track two running candidates at once, keeping the second **distinct**.

```cpp
int second_largest(const std::vector<int>& a);
```

- Return the largest value strictly below the maximum, or `-1` if there is none.
- `1 <= n <= 100000`, `0 <= a_i <= 10^9`. Values are non-negative, so `-1` is an unambiguous
  sentinel. O(n) is required.

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `counts_duplicates` | tie_resolution | A copy of the maximum can become the second largest |
| `no_demotion` | update_rule | A new maximum does not move the old maximum to second place |
| `skips_first` | index_range | Loop starts at index 1 without using `a[0]` |
| `zero_when_none` | output_contract | The answer starts at 0, so "none" is reported as 0 |

**Not modelled:**

- returning the smallest distinct value;
- looking only after the maximum's position;
- two errors at once.

## 3. Tests

There are 13 tests:

- 2 samples, including one with no answer;
- increasing and decreasing arrays;
- the answer in position 0;
- a repeated maximum including position 0;
- two distinct values;
- two equal values;
- a single element;
- 0 as a genuine answer;
- duplicates of both top values;
- two large generated arrays.

## 4. Discrimination and attribution checks

| Model | Detecting tests | Behaviour groups |
| --- | --- | --- |
| `counts_duplicates` | 7 | 3 |
| `no_demotion` | 5 | 3 |
| `skips_first` | 3 | 2 |
| `zero_when_none` | 3 | 2 |

**`zero_when_none` rests on one behaviour.** It differs from the reference only when no second
value exists. Its groups are separate only because other models fail differently on those
tests. The validator counts groups this way (ADR-019), so it is named unqualified. Its evidence
is still about a single observable: the output on "no answer" inputs.

**Alternative causes** (400 random inputs):

- **Sorting descending and taking the second element** is identical to `counts_duplicates` on
  every input. Both treat duplicates as separate values (`tie_resolution`), so the skill
  attribution is unique. The description names both routes.
- **"Largest value after the maximum's position"** is identical to `no_demotion` on 365 of 400
  inputs. The tests separate them: for example, `answer_first` gives 3 for `no_demotion` and -1
  for the alternative. So it is not an exact equivalence.

## 5. Role in the bank

- `recommendable = false`.
- `prerequisites = ["first-max-index"]`.

## 6. Held-out plan

There are 8 cases:

- 2 correct (sort and unique; two passes);
- 4 modelled, in different styles;
- 2 unmodelled.
