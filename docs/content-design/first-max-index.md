# Content design record: `first-max-index` (bank expansion batch A1, 2026-10-25)

> **Update 2026-10-26.** New content version `50798634a3ef…` (was `cb56cfeafe27…`). The record below describes the problem as designed and is unchanged.
>
> **Skill keys (ADR-034).** `skips_last` → `loop_bounds`. Declared skills are now `accumulator_init`, `tie_resolution`, `output_contract`, `loop_bounds`.
>
> **Banned names (ADR-035).** `banned_names` lists `std::max_element`; an attempt that names one gives no skill observations.

**Status.** Provisional, not research-validated. Built under the owner's instruction of
2026-10-25 10:09 to expand the bank beyond binary search. The design process and the skill keys
are described in [expansion-2026-10-25/README.md](expansion-2026-10-25/README.md). The matrix was
predicted natively, then measured in the sandbox; the measurement is authoritative:
[content report](../content-reports/first-max-index.md).

## 1. Learning objective and contract

A single scan for the position of the maximum, with the tie rule "first occurrence". This is the
entry problem of the `arrays` family.

```cpp
int first_max_index(const std::vector<int>& a);
```

- `1 <= n <= 100000`, `-10^9 <= a_i <= 10^9`, checked by the harness.
- Asks for O(n). `std::max_element` is ruled out in the statement, but not enforced.

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `max_starts_at_zero` | accumulator_init | Running maximum starts at 0, so all-negative arrays (or a maximum of 0 later) keep index 0 |
| `last_of_ties` | tie_resolution | Returns the last of several maxima |
| `skips_last` | index_range | Loop stops one element early |
| `returns_value` | output_contract | Returns the maximum value, not its index |

**Not modelled:**

- a 1-based index;
- two errors at once;
- `std::max_element`, which is correct.

## 3. Tests

There are 14 tests:

- 2 samples;
- the maximum first, last, or in the middle;
- all-negative arrays, with and without ties;
- a maximum of 0 after position 0;
- every element equal;
- a tie at both ends;
- small non-negative values, where index and value differ;
- a single element;
- two equal negative values;
- two large generated arrays (n = 100000).

## 4. Discrimination and attribution checks

**Native prediction** (equal to the sandbox measurement):

| Model | Detecting tests | Behaviour groups |
| --- | --- | --- |
| `max_starts_at_zero` | 5 | 3 |
| `last_of_ties` | 7 | 2 |
| `skips_last` | 3 | 2 |
| `returns_value` | 14 | 6 |

No two models are identical on the tests. `single` detects no model; it is kept as a
minimal-input check.

**Alternative causes** (400 random small inputs):

- **Reverse scan with `>`** (`alternatives/reverse_scan_strict.cpp`) is identical to
  `last_of_ties` on every input. Both are tie-resolution errors: the observable is "the last
  maximum wins". So the *skill* attribution is unique, but the *mechanism* is not. The model's
  description and hint therefore describe the behaviour, not the `>=` comparison.
- **A sentinel of -1 instead of 0** is identical to `max_starts_at_zero` on 399 of 400 inputs.
  It is the same skill.
- **A 1-based index** differs from every model on every input, so it is unmodelled.

## 5. Role in the bank

- `recommendable = false`. In this family, follow-ups fall back to a retry, and a pass gives
  action `none` (L21; see the expansion README).
- Attempts produce skill evidence for the researcher-only learner model under the new skill
  keys that the owner approved on 2026-10-25.

## 6. Held-out plan

There are 8 cases in `eval/heldout/first-max-index/`, all written by the models' author:

- 2 correct;
- 4 modelled, in different styles;
- 2 unmodelled.
