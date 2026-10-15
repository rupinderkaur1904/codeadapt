"""Follow-up evaluation: did the attempt after a recommendation meet its recorded criterion?

The verdict is about the follow-up attempt's tests only. It is never a claim about
learning: passing the follow-up's probes is consistent with improvement and with the
follow-up problem simply being easier (methodology §5). Each evaluation also records how
the follow-up problem relates to the index problem, so a retry, equivalent practice and a
transfer problem are never counted as the same kind of evidence.
"""

from __future__ import annotations

from codeadapt.adaptation.ledger import probe_result, tests_probing
from codeadapt.adaptation.models import (
    AttemptRecord,
    FollowupEvaluation,
    ProbeComparison,
    Recommendation,
    Relation,
    TestStatus,
    Verdict,
)
from codeadapt.content.models import ProblemSpec
from codeadapt.diagnosis.models import Outcome

METHOD = "criterion_check"
METHOD_VERSION = "1.1"  # 1.1: records the relation and states the scope of a pass

_NOT_EVIDENCE = {Outcome.COMPILE_ERROR, Outcome.EXECUTION_ERROR, Outcome.UNRELIABLE_EVIDENCE}

_SCOPE = {
    Relation.SAME_PROBLEM: "on a retry of the same problem, whose failing tests the student "
    "had already seen",
    Relation.EQUIVALENT_PRACTICE: "on an equivalent practice problem",
    Relation.TRANSFER: "on a problem linked as transfer; a single attempt is not evidence "
    "of transfer",
    Relation.OTHER: "on a problem with no curriculum link to the index problem",
}


def relation_of(index_spec: ProblemSpec | None, followup_spec: ProblemSpec) -> Relation:
    if index_spec is None:
        return Relation.OTHER
    if followup_spec.slug == index_spec.slug:
        return Relation.SAME_PROBLEM
    links = index_spec.curriculum
    if followup_spec.slug in links.transfer:
        return Relation.TRANSFER
    if followup_spec.slug in links.equivalents or followup_spec.family == index_spec.family:
        return Relation.EQUIVALENT_PRACTICE
    return Relation.OTHER


def evaluate_followup(
    recommendation: Recommendation,
    index: AttemptRecord,
    index_spec: ProblemSpec | None,
    followup: AttemptRecord,
    followup_spec: ProblemSpec,
) -> FollowupEvaluation:
    relation = relation_of(index_spec, followup_spec)

    def result(
        verdict: Verdict,
        reason: str,
        counts: tuple[int, int, int] = (0, 0, 0),
        table: tuple[ProbeComparison, ...] = (),
    ) -> FollowupEvaluation:
        passed, failed, excluded = counts
        return FollowupEvaluation(
            method=METHOD,
            method_version=METHOD_VERSION,
            verdict=verdict,
            reason=reason,
            passed=passed,
            failed=failed,
            excluded=excluded,
            probes=table,
            relation=relation,
        )

    criterion = recommendation.criterion
    if criterion is None:
        return result(Verdict.NOT_COMPARABLE, "no success criterion was recorded")
    if followup.outcome in _NOT_EVIDENCE:
        return result(
            Verdict.NOT_COMPARABLE,
            f"the follow-up produced no usable evidence ({followup.outcome.value})",
        )

    skills = set(criterion.skills)
    probes = sorted(p for p, ss in followup_spec.probes.items() if set(ss) & skills)
    table = tuple(
        ProbeComparison(
            probe=probe,
            skills=tuple(sorted(set(followup_spec.probes[probe]) & skills)),
            index=probe_result(index, index_spec, probe),
            followup=probe_result(followup, followup_spec, probe),
        )
        for probe in probes
    )
    statuses = [
        followup.tests[k] for k in tests_probing(followup_spec, skills) if k in followup.tests
    ]
    passed = statuses.count(TestStatus.PASSED)
    failed = statuses.count(TestStatus.FAILED)
    counts = (passed, failed, statuses.count(TestStatus.EXCLUDED))
    if passed + failed == 0:
        return result(
            Verdict.NOT_COMPARABLE,
            "no reliable follow-up test probes the targeted skills",
            counts,
            table,
        )
    if failed:
        return result(
            Verdict.CRITERION_NOT_MET,
            f"{failed} of {passed + failed} reliable follow-up tests probing the targeted "
            "skills failed",
            counts,
            table,
        )
    model_skill = {m.key: m.skill for m in followup_spec.error_models}
    if (
        followup.outcome is Outcome.HYPOTHESIS_SUPPORTED
        and followup.selected_model is not None
        and model_skill.get(followup.selected_model) in criterion.excluded_model_skills
    ):
        return result(
            Verdict.CRITERION_NOT_MET,
            "the follow-up was diagnosed with an error model of a targeted skill",
            counts,
            table,
        )
    return result(
        Verdict.CRITERION_MET,
        f"passed all {passed} reliable follow-up tests probing the targeted skills "
        f"{_SCOPE[relation]}. This meets the recorded test criterion; it is not evidence "
        "of mastery",
        counts,
        table,
    )
