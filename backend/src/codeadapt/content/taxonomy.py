"""The skill taxonomy: every key a problem may declare, and the keys that were retired.

A skill key links evidence across problems, so its definition must be the same wherever it is
declared. Keys are never reused: a retired key keeps its historical definition here, because
observations recorded under it (in the skill-map snapshot of an older content version) keep
that meaning. They are not converted to the keys that replaced it (ADR-034).
"""

from __future__ import annotations

from dataclasses import dataclass

TAXONOMY_VERSION = "2"

# Binary search (methodology §5) and the new families (ADR-033, revised by ADR-034).
ACTIVE: dict[str, str] = {
    "search_space_boundaries": "Initialising and updating the bounds of the search space so "
    "every candidate answer stays reachable.",
    "loop_termination": "Ensuring each iteration shrinks the search space so the loop terminates.",
    "equality_handling": "Choosing the comparison so equal elements land on the correct side "
    "of the boundary.",
    "problem_specification": "Returning what the specification asks for, including when the "
    "target is absent.",
    "accumulator_init": "Initialising (and re-initialising) a running best, minimum, maximum, "
    "count or sum to the value the first real element requires.",
    "tie_resolution": "Handling equal values as the specification says: which of several equal "
    "candidates wins, and whether duplicates count separately.",
    "output_contract": "Returning exactly what the specification asks for: an index or a value, "
    "a sentinel when there is no answer.",
    # ADR-034: the replacements for `index_range` and `update_rule`.
    "loop_bounds": "Visiting exactly the positions the task needs: a loop starts and ends at "
    "the right index and runs from the right end.",
    "range_inclusion": "Counting or summing over exactly the right set of positions: interval "
    "lengths, inclusive or exclusive ends, and whether an element may pair with itself or "
    "belongs to a side.",
    "window_maintenance": "Keeping a sliding window's state current: removing the element that "
    "leaves, and shrinking the window rather than restarting it.",
    "pointer_movement": "Moving the right pointer at each step of a two-pointer scan, and doing "
    "the comparison or write that each move depends on.",
    "running_state": "Keeping a tracked value current on every step and after the loop: a "
    "runner-up, the current run, a carry, a running prefix sum.",
}


@dataclass(frozen=True)
class RetiredSkill:
    definition: str  # its meaning while it was active; historical observations keep it
    retired: str  # date
    decision: str
    replaced_by: tuple[str, ...]


RETIRED: dict[str, RetiredSkill] = {
    "index_range": RetiredSkill(
        definition="Visiting exactly the valid positions: the loop's start and end cover every "
        "element once.",
        retired="2026-10-26",
        decision="ADR-034",
        replaced_by=("loop_bounds", "range_inclusion"),
    ),
    "update_rule": RetiredSkill(
        definition="Updating every piece of tracked state on each step (running candidates, "
        "pointers, window edges) so no candidate is lost.",
        retired="2026-10-26",
        decision="ADR-034",
        replaced_by=("window_maintenance", "pointer_movement", "running_state"),
    ),
}


def skill_problems(key: str, definition: str) -> list[str]:
    """Why `key` with `definition` may not be declared by a current problem (empty if it may)."""
    if key in RETIRED:
        r = RETIRED[key]
        return [
            f"skill {key!r} was retired on {r.retired} ({r.decision}); "
            f"use one of {', '.join(r.replaced_by)}"
        ]
    if key not in ACTIVE:
        return [f"unknown skill {key!r}: not in the skill taxonomy (content/taxonomy.py)"]
    if definition != ACTIVE[key]:
        return [f"skill {key!r}: definition differs from the taxonomy's"]
    return []
