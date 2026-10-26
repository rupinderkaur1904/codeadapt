# Content design record: `container-water` (bank expansion batch A2, 2026-10-25)

> **Update 2026-10-26.** New content version `e9fc3901bd29…` (was `bbac030fbe03…`). The record below describes the problem as designed and is unchanged.
>
> **Skill keys (ADR-034).** `moves_taller` → `pointer_movement`; `width_plus_one` → `range_inclusion`; `stops_before_adjacent` → `loop_bounds`. Declared skills are now `output_contract`, `loop_bounds`, `range_inclusion`, `pointer_movement`.
>
> **Positive-only skills (ADR-034).** `pointer_movement` has no model that can give negative evidence; the reason is recorded under `positive_only_skills`.

**Status.** Provisional, not research-validated. See
[expansion-2026-10-25/README.md](expansion-2026-10-25/README.md) and the
[content report](../content-reports/container-water.md).

## 1. Learning objective and contract

Two pointers with a greedy discard argument: the shorter line limits every container that uses
it.

```cpp
int max_water(const std::vector<int>& height);
```

- `2 <= n <= 100000`, `0 <= h_i <= 10000`, so every area is at most about 10^9 and fits in an
  `int`.

## 2. Error models

| Model | Skill | Error | Detecting tests / groups |
| --- | --- | --- | --- |
| `moves_taller` | update_rule | Moves the taller line's pointer. **Documented limitation: attribution not unique (L20)** | 9 / 2 |
| `width_plus_one` | index_range | Width counted as `hi - lo + 1` | 13 / 5 |
| `uses_taller_height` | output_contract | Water level from the taller line | 10 / 3 |
| `stops_before_adjacent` | index_range | Loops while `lo + 1 < hi`, so neighbouring lines are never paired | 3 / 2 |

**Why `moves_taller` carries a `known_limitation`.** If the taller pointer moves, the shorter
line stays, the width shrinks, and the level can never rise above the shorter line. So no
container ever beats the outermost pair. The model is therefore **output-identical on every
valid input** to "measure only the two outer lines", which is a misread specification. The
design check confirmed it on 400 random inputs.

The attribution to `update_rule` is not unique. So the diagnosis is kept and shown as one
possible cause, and it adds no skill evidence (ADR-032 route). It is listed in
`NON_UNIQUE_ATTRIBUTION` in `test_demo_content`.

## 3. Tests

There are 13 tests:

- 2 samples;
- the outer pair as the best;
- tall lines inside short ones;
- adjacent tallest lines;
- equal tall lines at the end;
- uneven ends;
- zeros;
- increasing and decreasing heights;
- equal heights;
- two large generated skylines.

## 4. Other attribution checks

- **A double loop that counts lines** is identical to `width_plus_one`. It is the same skill.
- **The two tallest lines** agrees with `moves_taller` on 104 of 400 inputs, and is otherwise
  unmodelled.

## 5. Role and held-out plan

- `recommendable = false`; `prerequisites = ["closest-pair-sum"]`.
- There are 8 held-out cases:
  - 2 correct;
  - 4 modelled;
  - 2 unmodelled.
