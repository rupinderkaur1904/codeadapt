"""A fixed set of synthetic histories over the three original binary-search problems.

Used by the policy 1.3 regression test (CE1 decision E2): every recommendation for these
histories must be identical to what policy 1.2 produced before any non-recommendable
problem existed. The golden file was generated from commit 89a7803 (policy 1.2) with
`python -m tests.unit.policy_cases > tests/fixtures/policy_v1_golden.json`, run from
`backend/` against that commit's source.

These are synthetic attempts that exercise every rule; they are not learner data.
"""

from __future__ import annotations

import itertools
import json
import sys
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from codeadapt.adaptation import AttemptRecord, PolicyV1, TestStatus
from codeadapt.content.models import ProblemSpec
from codeadapt.diagnosis import Outcome

ORIGINAL = ("count-occurrences", "last-less-than", "lower-bound")
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def attempts_for(spec: ProblemSpec) -> Iterator[tuple[Outcome, dict[str, Any]]]:
    """One attempt per rule, model and candidate pair on `spec`."""
    yield Outcome.NO_FAILURE_OBSERVED, {}
    yield Outcome.COMPILE_ERROR, {}
    yield Outcome.UNMODELLED_BEHAVIOUR, {"failing": (spec.tests[0].key,)}
    for m in spec.error_models:
        failing = tuple(t.key for t in spec.tests if m.key in (t.distinguishes or ()))
        yield Outcome.HYPOTHESIS_SUPPORTED, {"model": m.key, "failing": failing}
    for a, b in itertools.combinations([m.key for m in spec.error_models], 2):
        yield Outcome.AMBIGUOUS, {"candidates": (a, b), "failing": (spec.tests[0].key,)}


def record(spec: ProblemSpec, n: int, outcome: Outcome, kw: dict[str, Any]) -> AttemptRecord:
    tests: dict[str, TestStatus] = {}
    if outcome is not Outcome.COMPILE_ERROR:
        tests = {
            t.key: TestStatus.FAILED if t.key in kw.get("failing", ()) else TestStatus.PASSED
            for t in spec.tests
        }
    model = kw.get("model")
    return AttemptRecord(
        submission_id=f"s{n}",
        problem_slug=spec.slug,
        created_at=T0 + timedelta(minutes=n),
        outcome=outcome,
        selected_model=model,
        candidates=kw.get("candidates", (model,) if model else ()),
        tests=tests,
    )


def histories(problems: Mapping[str, ProblemSpec]) -> Iterator[list[AttemptRecord]]:
    """Every single attempt, then each one after a pass or a failure on another problem."""
    singles = [
        (problems[slug], outcome, kw)
        for slug in ORIGINAL
        for outcome, kw in attempts_for(problems[slug])
    ]
    for spec, outcome, kw in singles:
        yield [record(spec, 0, outcome, kw)]
    for spec, outcome, kw in singles:
        for prior in ORIGINAL:
            p = problems[prior]
            yield [record(p, 0, Outcome.NO_FAILURE_OBSERVED, {}), record(spec, 1, outcome, kw)]
    # Every original problem passed, in each order: the "family exhausted" case.
    for order in itertools.permutations(ORIGINAL):
        yield [record(problems[s], i, Outcome.NO_FAILURE_OBSERVED, {}) for i, s in enumerate(order)]


def recommendations(
    problems: Mapping[str, ProblemSpec], version: str = "1.4"
) -> list[dict[str, Any]]:
    # The golden file pins policy 1.2-1.4 behaviour; policy 1.5 has its own fixture.
    policy = PolicyV1(version=version)
    out = []
    for history in histories(problems):
        rec = policy.recommend(history[-1], history, problems)
        out.append(rec.model_dump(mode="json", exclude={"policy_version"}))
    return out


if __name__ == "__main__":
    from codeadapt.content import load_catalogue
    from tests.paths import DEMO_CONTENT

    specs = {p.spec.slug: p.spec for p in load_catalogue(DEMO_CONTENT)}
    version = sys.argv[1] if len(sys.argv) > 1 else "1.4"
    print(json.dumps(recommendations(specs, version), indent=1, sort_keys=True))
