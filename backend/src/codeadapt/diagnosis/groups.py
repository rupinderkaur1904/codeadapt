"""Behaviour groups: tests that every modelled program passes together or fails together.

Two tests in the same group give the diagnosis the same information, however many there
are, so evidence strength is counted in groups, not tests (docs/content-design/README.md).
Groups are relative to the modelled programs: adding a model can split a group.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from codeadapt.evidence.signature import Signature


def detection_patterns(
    reference: Mapping[str, Signature | None],
    models: Mapping[str, Mapping[str, Signature | None]],
) -> dict[str, frozenset[str]]:
    """For each test, the set of models whose behaviour differs from the reference on it."""
    return {
        test: frozenset(k for k, pred in models.items() if pred.get(test) != ref)
        for test, ref in reference.items()
    }


def count_groups(tests: Iterable[str], patterns: Mapping[str, frozenset[str]]) -> int:
    """Number of distinct behaviour groups among `tests`."""
    return len({patterns[t] for t in tests})


def group_tests(
    patterns: Mapping[str, frozenset[str]], order: Iterable[str]
) -> list[tuple[frozenset[str], tuple[str, ...]]]:
    """Every group as (detecting models, its tests), in first-test order of `order`."""
    groups: dict[frozenset[str], list[str]] = {}
    for test in order:
        groups.setdefault(patterns[test], []).append(test)
    return [(pattern, tuple(tests)) for pattern, tests in groups.items()]
