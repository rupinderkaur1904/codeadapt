# LM1 sensitivity to the assumed BKT parameters (2026-10-17)

This is a **technical check, not validation.** It measures how much a displayed estimate
depends on the assumed parameters. It does not show whether any parameter set describes
real learners.

To reproduce, run this from `backend/`:

```
uv run python ../docs/evaluation/bkt-sensitivity-2026-10-17/sensitivity.py
```

The sequences are the ones possible on the current bank: at most one counted observation
per problem version and three problems. C is correct, I is incorrect, in order. The grid
has 81 parameter sets:
- P(L0) ∈ {0.1, 0.3, 0.5}
- P(T) ∈ {0.05, 0.1, 0.2}
- P(G) ∈ {0.1, 0.2, 0.3}
- P(S) ∈ {0.05, 0.1, 0.2}

| Sequence | Assumed-1 | Grid min | Grid max | Spread |
| --- | ---: | ---: | ---: | ---: |
| C | 0.693 | 0.267 | 0.924 | 0.657 |
| I | 0.146 | 0.056 | 0.378 | 0.322 |
| CC | 0.919 | 0.518 | 0.993 | 0.475 |
| IC | 0.491 | 0.204 | 0.847 | 0.643 |
| CCC | 0.983 | 0.754 | 0.999 | 0.245 |
| ICC | 0.831 | 0.468 | 0.982 | 0.515 |
| CIC | 0.691 | 0.250 | 0.969 | 0.719 |
| IIC | 0.440 | 0.196 | 0.808 | 0.613 |
| CCI | 0.629 | 0.140 | 0.966 | 0.827 |
| III | 0.115 | 0.053 | 0.294 | 0.241 |

The next table varies one parameter at a time, holding the others at their assumed values:

| Varied parameter | ICC range | CCC range |
| --- | --- | --- |
| P(L0) (0.1, 0.3, 0.5) | 0.793–0.874 | 0.945–0.992 |
| P(T) (0.05, 0.1, 0.2) | 0.733–0.921 | 0.979–0.988 |
| P(G) (0.1, 0.2, 0.3) | 0.712–0.946 | 0.946–0.998 |
| P(S) (0.05, 0.1, 0.2) | 0.822–0.837 | 0.976–0.985 |

**Reading.**
- On sequences of three or fewer observations, the displayed P(known) can move by up to
  0.83 within this plausible-looking grid.
- P(G) and P(T) matter most.
- Three correct observations give 0.98 under the assumed set, although each `correct` only
  means that the probing tests passed.

The estimates are therefore mostly a function of the assumptions. That is why they stay
researcher-only and labelled "estimated under assumed parameters".
