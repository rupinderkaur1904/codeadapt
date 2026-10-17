"""Sensitivity of LM1 estimates to the assumed BKT parameters (technical check only).

Run from backend/:  uv run python ../docs/evaluation/bkt-sensitivity-2026-10-17/sensitivity.py

For each observation sequence a learner can produce on the current bank (at most one
counted observation per problem version, three problems), compute P(known) under every
parameter set in a grid around `bkt-params-assumed-1`, and report the spread. This says
how much the displayed number depends on the assumptions. It says nothing about whether
any parameter set describes real learners.
"""

from __future__ import annotations

import itertools

from codeadapt.learner import ASSUMED_PARAMS_1, BktParams, update

GRID = {
    "p_init": (0.1, 0.3, 0.5),
    "p_learn": (0.05, 0.1, 0.2),
    "p_guess": (0.1, 0.2, 0.3),
    "p_slip": (0.05, 0.1, 0.2),
}
SEQUENCES = ["C", "I", "CC", "IC", "CCC", "ICC", "CIC", "IIC", "CCI", "III"]


def trace(seq: str, params: BktParams) -> float:
    p = params.p_init
    for obs in seq:
        p = update(p, obs == "C", params)
    return p


def main() -> None:
    grid = [
        BktParams(name="grid", **dict(zip(GRID, values, strict=True)))
        for values in itertools.product(*GRID.values())
    ]
    print(f"grid: {len(grid)} parameter sets; " + ", ".join(f"{k} {v}" for k, v in GRID.items()))
    print()
    print("| Sequence | Assumed-1 | Grid min | Grid max | Spread |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for seq in SEQUENCES:
        values = [trace(seq, p) for p in grid]
        lo, hi = min(values), max(values)
        print(
            f"| {seq} | {trace(seq, ASSUMED_PARAMS_1):.3f} | {lo:.3f} | {hi:.3f} | {hi - lo:.3f} |"
        )
    print()
    # One parameter at a time, the others at their assumed values: which assumption matters.
    base = ASSUMED_PARAMS_1.model_dump()
    print("| Varied parameter | ICC range | CCC range |")
    print("| --- | --- | --- |")
    for name, values in GRID.items():
        sets = [BktParams(**{**base, name: v}) for v in values]
        icc = [trace("ICC", p) for p in sets]
        ccc = [trace("CCC", p) for p in sets]
        print(
            f"| {name} {values} | {min(icc):.3f}–{max(icc):.3f} | {min(ccc):.3f}–{max(ccc):.3f} |"
        )


if __name__ == "__main__":
    main()
