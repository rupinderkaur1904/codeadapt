# Content design record: `second-largest` (bank expansion batch A1, 2026-10-25)

> **Update 2026-10-26.** New content version `6f9032b8d8b8…` (was `15b0c500f154…`). The record below describes the problem as designed and is unchanged.
>
> **Skill keys (ADR-034).** `no_demotion` → `running_state`; `skips_first` → `loop_bounds`. Declared skills are now `tie_resolution`, `output_contract`, `loop_bounds`, `running_state`.

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
- **"Largest value after the maximum's position"** (`alternatives/max_of_rest.cpp`) is
  identical to `no_demotion` on 365 of 400 random inputs. **Correction:** the first version of
  this record said the tests separate the two, citing `answer_first`. That was wrong: both give
  3 there, and the two programs agree on every original test. The held-out case
  `after_max_only.cpp` (truth `unmodelled`) was therefore named `no_demotion` (see §7).

## 5. Role in the bank

- `recommendable = false`.
- `prerequisites = ["first-max-index"]`.

## 6. Held-out plan

There are 8 cases:

- 2 correct (sort and unique; two passes);
- 4 modelled, in different styles;
- 2 unmodelled.

## 7. Change after the held-out evaluation (2026-10-25)

**What happened.** The first held-out evaluation, on content version 1, named the unmodelled case
`after_max_only.cpp` as `no_demotion`. This is a wrong diagnosis, and it is kept on record in
`docs/evaluation/expansion-2026-10-25/second-largest.md`. The design tool had only compared the
alternatives on random inputs. It now also reports any alternative that matches a model on every
test.

**What changed.** The test `answer_before_max` (`[5, 3, 9]`, answer 5) was added. It separates
the two programs: `no_demotion` gives 3, and the alternative gives -1. This creates a new content
version. The held-out set was re-run on it and recorded separately (`second-largest-v2.*`).

**What the re-run can and cannot show.** The change was made *after* seeing a held-out result. So
that case no longer counts as an independent check of the new version. The re-run only shows
that the added test does what it was designed to do.
