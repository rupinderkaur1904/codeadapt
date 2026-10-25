# Content design record: `stock-profit` (bank expansion batch A1, 2026-10-25)

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) and the
[content report](../content-reports/stock-profit.md).

## 1. Learning objective and contract

A running minimum combined with a best-so-far answer, where order matters: the purchase must
come before the sale.

```cpp
int max_profit(const std::vector<int>& prices);
```

- Return the best profit, or 0 when no trade gains.
- `1 <= n <= 100000`, `1 <= p_i <= 10000`, so the profit fits easily in an `int`. O(n) is
  required.

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `ignores_order` | output_contract | Overall maximum minus overall minimum. **Documented limitation: attribution not unique (L20)** |
| `allows_loss` | output_contract | Must trade, so a falling market gives a negative profit, and a single day gives `INT_MIN` |
| `misses_last_day` | index_range | Loop stops one day early |

**`ignores_order` carries a `known_limitation`.** Two causes give the same output on every valid
input, and they belong to different skills:

- sorting the prices: a misread specification;
- tracking the overall minimum and maximum separately: an update error.

So the model takes the ADR-032 route: the diagnosis is kept and shown as qualified, and it adds
no skill evidence. It is mapped to `output_contract` for the record. `test_demo_content`
lists it under `NON_UNIQUE_ATTRIBUTION`.

**Considered and dropped: `min_from_zero`** (the running minimum starts at 0). It is identical to
"return the highest price" on every input, so its `accumulator_init` attribution would not be
unique. Rather than add a model that can never give evidence, it is left unmodelled. It is one
of the held-out unmodelled cases.

**Not modelled:**

- trading only on consecutive days;
- O(n^2) pair checks, which are correct but give `non_termination_observed` on the large tests.

## 3. Tests

There are 13 tests:

- 2 samples (typical, falling);
- the best sale on the last day;
- the global minimum after the global maximum, in several shapes;
- flat prices;
- a single day;
- two days, rising and falling;
- a dip followed by a final rise;
- a large rising market (n = 10000);
- a large sawtooth (n = 100000).

## 4. Discrimination

| Model | Detecting tests | Behaviour groups |
| --- | --- | --- |
| `ignores_order` | 7 | 3 |
| `allows_loss` | 3 | 2 |
| `misses_last_day` | 4 | 2 |

`dip_then_last_rise` was added to give `misses_last_day` a second behaviour group.

## 5. Role in the bank

- `recommendable = false`.
- `prerequisites = ["first-max-index"]`.

## 6. Held-out plan

There are 7 cases:

- 2 correct (suffix maximum; maximum-sum run of differences);
- 3 modelled. `sorted_spread` is the documented non-unique route of `ignores_order`.
- 2 unmodelled (consecutive days; low from zero).
