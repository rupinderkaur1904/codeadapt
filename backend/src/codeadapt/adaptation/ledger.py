"""The learner evidence ledger: per skill, the chronological probe observations.

There is deliberately no latent "mastery" variable (methodology §5): the ledger is a
reorganisation of stored evidence, nothing more.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from codeadapt.adaptation.models import AttemptRecord, ProbeEvidence, ProbeResult, TestStatus
from codeadapt.content.models import ProblemSpec

Ledger = dict[str, tuple[ProbeEvidence, ...]]


def build_ledger(attempts: Sequence[AttemptRecord], problems: Mapping[str, ProblemSpec]) -> Ledger:
    """Attribute every recorded test outcome to the skills its probes name.

    Attempts on problems missing from `problems`, and test keys the current spec does not
    define (an older content version), are skipped rather than guessed.
    """
    entries: dict[str, list[ProbeEvidence]] = {}
    for attempt in sorted(attempts, key=lambda a: a.created_at):
        spec = problems.get(attempt.problem_slug)
        if spec is None:
            continue
        by_key = {t.key: t for t in spec.tests}
        for key, status in attempt.tests.items():
            test = by_key.get(key)
            if test is None:
                continue
            for skill in sorted(spec.skills_probed_by(test)):
                entries.setdefault(skill, []).append(
                    ProbeEvidence(
                        skill=skill,
                        problem_slug=attempt.problem_slug,
                        test_key=key,
                        submission_id=attempt.submission_id,
                        status=status,
                    )
                )
    return {skill: tuple(items) for skill, items in entries.items()}


def reliable_count(ledger: Ledger, skill: str) -> int:
    return sum(1 for e in ledger.get(skill, ()) if e.status is not TestStatus.EXCLUDED)


def tests_probing(spec: ProblemSpec, skills: set[str] | frozenset[str]) -> list[str]:
    return [t.key for t in spec.tests if spec.skills_probed_by(t) & skills]


def probe_result(
    attempt: AttemptRecord | None, spec: ProblemSpec | None, probe: str
) -> ProbeResult:
    """Aggregate an attempt's outcomes over the tests carrying `probe`."""
    if attempt is None or spec is None or probe not in spec.probes:
        return ProbeResult.NOT_PROBED
    statuses = [
        attempt.tests[t.key] for t in spec.tests if probe in t.probes and t.key in attempt.tests
    ]
    if not statuses:
        return ProbeResult.NOT_PROBED
    if TestStatus.FAILED in statuses:
        return ProbeResult.FAILED
    if TestStatus.PASSED in statuses:
        return ProbeResult.PASSED
    return ProbeResult.EXCLUDED
