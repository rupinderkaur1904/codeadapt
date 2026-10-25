# Content design record: `min-capacity` (G3, CE1.3, built during CE2)

**Status and order.**

- This is the G3 transfer problem approved in the CE1 proposal (E3). CE1.3 was paused on
  2026-10-21. It was built on 2026-10-24 under the owner's overnight instruction to expand the
  problem bank, which this record reads as resuming CE1.3.
- The record was written together with the content.
- The matrix was predicted by native runs (a scratch tool, not committed), then measured in the
  sandbox. The measurement is authoritative: [content report](../content-reports/min-capacity.md).
- The held-out cases were committed after the content and before `codeadapt-eval` ran on them.

## 1. Learning objective

Binary search over the **answer space** with a monotone feasibility check: find the smallest
capacity that ships ordered packages within `days` days. The array is not searched directly.
This is the first problem in the bank where the searched range is a range of candidate answers.

**Contract.**

```cpp
int min_capacity(const std::vector<int>& weights, int days);
```

- `1 <= n <= 100000`, `1 <= w_i <= 10000`, `1 <= days <= n`, all checked by the harness.
- The answer lies in `[max w, sum w]` and is at most 10^9, so it fits in an `int`.
- Asks for O(n log W). This is not enforced, but a linear scan over capacities times out on the
  large tests (§4).

**Skills.** The four existing keys; no new skill is proposed. The mapping of each model to a
skill is a modelling assumption, as everywhere in the bank:

| Skill | How it appears here |
| --- | --- |
| `search_space_boundaries` | The lower bound of the answer space is the heaviest package, not 1. |
| `loop_termination` | Infeasible capacities must move `lo` past `mid`. |
| `equality_handling` | A day loaded *exactly* to capacity, and *exactly* `days` days, are both allowed. |
| `problem_specification` | The packages ship in the given order. |

Mapping the two exact-boundary errors to `equality_handling` stretches that skill's description
("equal elements land on the correct side"). The underlying idea, choosing `<` against `<=` at
a boundary, is the same. A reviewer may prefer a separate skill. Per the CE1 rule, I have **not**
added one; this is flagged here as evidence for the owner.

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `lo_init_one` | search_space_boundaries | `lo = 1`, so a capacity below the heaviest package can be accepted |
| `hi_skips_candidate` | search_space_boundaries | `hi = mid - 1` after a feasible capacity in a half-open loop |
| `no_progress_update` | loop_termination | `lo = mid` after an infeasible capacity (time limit) |
| `strict_day_limit` | equality_handling | Feasible only when `days_needed < days` |
| `full_day_overflows` | equality_handling | New day when `load + x >= cap`, so an exactly full day is rejected |
| `sorts_weights` | problem_specification | Sorts the packages before checking feasibility |

**Not modelled.**

- `(lo + hi) / 2` overflow. With `sum w` up to 10^9, `lo + hi` can exceed `INT_MAX` on
  `large_one_day`. This is a real error, but its skill mapping is unclear, so it is not
  modelled. The outcome would be unmodelled behaviour or a time limit.
- Linear scan over capacities. This is correct but times out on the large tests, which gives
  `non_termination_observed` under v1.3 with no name.
- Two errors at once.

## 3. Tests

There are 19 tests:

- 2 samples;
- answer = total weight: one day, two packages on one day, and large;
- answer = heaviest package: one day each, a dominant heavy package, equal packages, two
  packages on two days, and large;
- exact fills: pairs of 5s, uniform weights, and a periodic large test;
- order-dependent tests where sorting changes the answer;
- uneven runs and decreasing weights;
- a single package.

## 4. Measured discrimination and ambiguity

Sandbox validation result: `ok`, with no single-group warnings. The measured matrix equals the
native prediction.

- Every model is detected by at least 3 tests in at least 2 behaviour groups.
- `lo_init_one` is detected only where the answer is the heaviest package. Its outputs are
  below `max w`, which no other model produces.
- **The two equality models overlap heavily.** `strict_day_limit` fails 14 tests and
  `full_day_overflows` fails 12. Their failing sets and outputs differ (for example
  `heavy_dominates` and `two_two_days` fail only for `strict_day_limit`), so they separate.
- `no_progress_update` is seen only as time limits and is never named under v1.3 (ADR-027).
- `single_package` detects no model. It is kept as a minimal-input check.

## 5. Role in the bank and recommendation

- `recommendable = false` (decision E2). Policy 1.4 and its golden test are unchanged.
- Attempts are diagnosed and produce skill evidence for the researcher-only learner model.
- `prerequisites = ["first-true", "lower-bound"]`. first-true is the predicate form of the same
  search.
- **Transfer.** A pass here shows that the four skills' observations occur in a new context. It
  cannot show that learning transfers (CE1 proposal, Risks).

## 6. Held-out plan

There are 8 cases in `eval/heldout/min-capacity/`, all written by the models' author:

- 2 correct;
- 4 modelled in different styles;
- 2 unmodelled.

## 7. Change after review: non-unique attribution (2026-10-25, ADR-032)

**Change.** On the owner's decision (option b, L20), `strict_day_limit` and
`full_day_overflows` now carry a `known_limitation`.

**Why.** Each is output-identical, on every valid input, to a program with a counting or
specification error (docs/reviews/2026-10-25/skill-mapping-review.md).

**Effect.**

- Their diagnoses are kept and traced.
- They are shown to the student as one possible cause.
- They add no `equality_handling` evidence.

**Versioning.** This edit created a new content version. The earlier version's held-out
evaluation (docs/evaluation/ce2-2026-10-24/) is historical and unchanged. The problem
remains provisional and not research-validated.
