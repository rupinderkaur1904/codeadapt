"""Observation capacity of the demo bank and BKT sensitivity on it (technical check only).

Run from backend/:  uv run python ../docs/evaluation/ce1.1-2026-10-18/capacity.py

Capacity: for each skill, how many problems can give a counted observation (one per problem
version, LM1 rule L1) and how many can give an `incorrect` one. An `incorrect` observation
needs an unqualified diagnosis of a model of that skill; content validation guarantees that
a model without a `known_limitation` has at least two behaviour groups, so such models are
the ones counted here. This describes what the content allows, not what any learner did.

Sensitivity: P(known) over the same 81-point grid as docs/evaluation/bkt-sensitivity-
2026-10-17, for sequences one observation longer than the previous bank allowed. It says
how much a displayed number depends on the assumptions, not whether any parameter set
describes real learners.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

from codeadapt.content import load_catalogue
from codeadapt.learner import ASSUMED_PARAMS_1, BktParams, update

GRID = {
    "p_init": (0.1, 0.3, 0.5),
    "p_learn": (0.05, 0.1, 0.2),
    "p_guess": (0.1, 0.2, 0.3),
    "p_slip": (0.05, 0.1, 0.2),
}
SEQUENCES = ["CCCC", "ICCC", "IICC", "CICC", "CCCI", "IIII"]


def trace(seq: str, params: BktParams) -> float:
    p = params.p_init
    for obs in seq:
        p = update(p, obs == "C", params)
    return p


def main(content: Path) -> None:
    specs = [p.spec for p in load_catalogue(content)]
    skills = sorted({s for spec in specs for s in spec.skills})
    print("| Skill | Problems probing it (max counted) | Problems that can give `incorrect` |")
    print("| --- | --- | --- |")
    for skill in skills:
        probing = [s.slug for s in specs if any(skill in s.skills_probed_by(t) for t in s.tests)]
        failing = [
            f"{s.slug} ({', '.join(m.key for m in ms)})"
            for s in specs
            if (ms := [m for m in s.error_models if m.skill == skill and not m.known_limitation])
        ]
        print(
            f"| {skill} | {len(probing)}: {', '.join(probing)} | "
            f"{len(failing)}: {'; '.join(failing) or 'none'} |"
        )
    print()
    grid = [
        BktParams(name="grid", **dict(zip(GRID, values, strict=True)))
        for values in itertools.product(*GRID.values())
    ]
    print("| Sequence | Assumed-1 | Grid min | Grid max | Spread |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for seq in SEQUENCES:
        values = [trace(seq, p) for p in grid]
        lo, hi = min(values), max(values)
        print(
            f"| {seq} | {trace(seq, ASSUMED_PARAMS_1):.3f} | {lo:.3f} | {hi:.3f} | {hi - lo:.3f} |"
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../content/demo"))
