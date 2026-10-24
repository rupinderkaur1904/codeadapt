# CE1.4 family report: observation capacity and BKT sensitivity (2026-10-24)

**Technical measurements only.** Nothing here estimates a real learner, validates a BKT
parameter or shows learning. The parameter set is still the assumed `bkt-params-assumed-1`.

**Command** (from `backend/`):

```
uv run python ../docs/evaluation/ce1.4-2026-10-24/capacity.py
```

Output: [output.md](output.md). The bank is the 12 binary-search problems on this branch. 3 of
them are recommendable by policy v1. The others are `recommendable = false` under decision E2,
but they still feed the learner model.

## Observation capacity per skill

Under LM1 (L1), a learner gets at most one counted observation per problem version.

| Skill | Max counted observations | Problems that can give `incorrect` |
| --- | --- | --- |
| equality_handling | 8 | 8 |
| loop_termination | 12 | 5 |
| problem_specification | 12 | 12 |
| search_space_boundaries | 11 | 9 |

These are upper bounds. A problem only counts as able to give `incorrect` if one of its models
on that skill can be named without qualification. That excludes:

- models with a documented collision;
- models that are time-limit-only in the measured content report, which v1.3 never names
  (ADR-027).

The 2026-10-17 audit found **at most 3 observations per skill** on the original bank, and only
one possible `incorrect` for `search_space_boundaries`. Both ceilings are now higher.

## Sensitivity of P(known) to the assumed parameters

The grid is the same as `docs/evaluation/bkt-sensitivity-2026-10-17/`: 81 parameter sets.

| Sequence | min | max | assumed |
| --- | --- | --- | --- |
| C | 0.267 | 0.924 | 0.693 |
| CC | 0.518 | 0.993 | 0.919 |
| CCC | 0.754 | 0.999 | 0.983 |
| ICC | 0.468 | 0.982 | 0.831 |
| CCCCC | 0.961 | 1.000 | 0.999 |
| ICCCC | 0.877 | 1.000 | 0.992 |

## How to read this

- **The spread narrows with more observations, but that is not validation.** It narrows
  because BKT without forgetting drives P(known) towards 1 after a run of correct
  observations, whatever the parameters. Agreement across the grid at 5+ observations says the
  model saturates. It does not say the estimate is right.
- **`correct` observations are weak evidence** (rule C). A pass on every probing test is not
  a demonstration of the skill. The critical review (2026-10-21) already noted that a linear
  scan reaches about 0.98 after 3 problems. With more problems, such a program saturates
  sooner.
- **The larger bank makes the estimates more optimistic, not more trustworthy.** The display
  threshold (≥ 3 counted observations from ≥ 2 problems) is reached sooner. Its label,
  "estimated under assumed parameters", remains essential.
- **No change was made** to parameters, the threshold or any policy.
