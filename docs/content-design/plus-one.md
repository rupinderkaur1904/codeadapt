# Content design record: `plus-one` (bank expansion batch A2, 2026-10-25)

> **Update 2026-10-26.** New content version `a7518c266db6…` (was `53ce6c46a11b…`). The record below describes the problem as designed and is unchanged.
>
> **Skill keys (ADR-034).** `single_carry` → `running_state`; `adds_at_front` → `loop_bounds`; `carry_never_cleared` → `running_state`. Declared skills are now `output_contract`, `loop_bounds`, `running_state`.

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) and the
[content report](../content-reports/plus-one.md), which is authoritative.

## 1. Learning objective and contract

Process an array from the back, carrying state (the carry) from one position to the next.

```cpp
std::vector<int> plus_one(const std::vector<int>& digits);
```

- `1 <= n <= 100000` decimal digits, most significant first, with no leading zero.
- The result is printed in full when it has at most 40 digits. Otherwise it is printed as its
  length, first and last digit, and a fixed polynomial hash, so long results compare exactly
  without large outputs.

## 2. Error models

| Model | Skill | Error | Detecting tests / groups |
| --- | --- | --- | --- |
| `single_carry` | update_rule | Carries into the next digit only once, so a second 9 becomes 10 | 5 / 3 |
| `no_new_digit` | output_contract | Drops the carry out of the top digit, so 999 becomes 000 | 3 / 2 |
| `adds_at_front` | index_range | Treats `digits[0]` as the least significant digit | 12 / 6 |
| `carry_never_cleared` | update_rule | Adds 1 to every digit | 7 / 2 |

**Not modelled:**

- no carry at all;
- converting to a built-in integer, which overflows on long inputs.

## 3. Tests

There are 13 tests:

- 2 samples;
- one carry, and a carry through 5 digits;
- all nines, and the single digit 9;
- 0;
- nines at the front with no carry;
- a zero that stops the carry;
- 19;
- 100000 nines;
- a 99999-digit number ending in 9.

## 4. Attribution checks

- **Reversing the digits, adding, and not reversing back** agrees with `adds_at_front` on 173 of
  400 random inputs. The outputs differ on the others, so this is not an exact equivalence.
- **No exact equivalence was found.** No alternative was identical to a model on every input.

## 5. Role and held-out plan

- `recommendable = false`; family `arrays`.
- There are 8 held-out cases:
  - 2 correct;
  - 4 modelled;
  - 2 unmodelled.
