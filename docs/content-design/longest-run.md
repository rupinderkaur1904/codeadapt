# Content design record: `longest-run` (bank expansion batch A1, 2026-10-25)

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) and the
[content report](../content-reports/longest-run.md).

## 1. Learning objective and contract

Maintain a counter that resets correctly, and finish the last run.

```cpp
int longest_run(const std::vector<int>& a);
```

- Return the length of the longest block of equal consecutive values.
- `1 <= n <= 100000`, `-10^9 <= a_i <= 10^9`. O(n) is required.

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `reset_to_zero` | accumulator_init | A new run restarts at 0, so runs after the first are one short |
| `last_run_unchecked` | update_rule | The best is updated only when a run ends, so the final run is never compared |
| `returns_value` | output_contract | Returns the value of the longest run, not its length |
| `compares_to_first` | update_rule | Compares with `a[0]` instead of the neighbour |

**Not modelled:**

- counting equal pairs (every answer one short);
- counting the most frequent value anywhere;
- two errors at once.

## 3. Tests

There are 13 tests:

- 2 samples;
- the first run longest;
- every value equal;
- every value distinct;
- a single element;
- two equal values;
- values that reappear after a gap;
- a later run of `a[0]`'s value;
- a tie between the first and last run;
- negative values;
- two large generated arrays (one run; no repeats).

## 4. Discrimination and attribution checks

| Model | Detecting tests | Behaviour groups |
| --- | --- | --- |
| `reset_to_zero` | 5 | 4 |
| `last_run_unchecked` | 6 | 3 |
| `returns_value` | 13 | 6 |
| `compares_to_first` | 3 | 2 |

**Alternative causes:**

- **`best = 1` instead of 0 in `last_run_unchecked`** agrees with that model on 340 of 400
  random inputs. It differs only when the array is a single run.
- **Counting equal pairs** agrees with `reset_to_zero` on 184 of 400 inputs, and is separated by
  the tests (for example `first_run_longest`).

Neither alternative is an exact equivalence.

## 5. Role in the bank

- `recommendable = false`.
- `prerequisites = ["first-max-index"]`.

## 6. Held-out plan

There are 8 cases:

- 2 correct;
- 4 modelled;
- 2 unmodelled (most frequent value; equal pairs).
