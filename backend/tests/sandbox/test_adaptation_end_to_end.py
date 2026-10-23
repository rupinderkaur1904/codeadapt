"""M6 acceptance: diagnosis -> recommendation -> follow-up evaluation, through the sandbox.

A scripted synthetic learner (ADR-008) submits error-model mutants and references. This
checks the mechanism end to end; it is not evidence that the policy helps anyone learn.
"""

from __future__ import annotations

from tests.paths import DEMO_CONTENT
from tests.sandbox.test_end_to_end import STUDENT, Harness


def source(slug: str, file: str) -> str:
    return (DEMO_CONTENT / slug / file).read_text()


async def test_recommendation_and_followup_end_to_end(harness: Harness) -> None:
    # 1. A supported equality-handling error on lower-bound.
    _, trace = await harness.submit(source("lower-bound", "error_models/upper_bound_confusion.cpp"))
    assert trace["diagnosis"]["outcome"] == "hypothesis_supported"
    rec = trace["recommendation"]
    assert (rec["rule"], rec["action"], rec["problem_slug"]) == (
        "hypothesis_supported",
        "new_problem",
        "count-occurrences",
    )
    assert rec["target_skills"] == ["equality_handling"]
    assert trace["followup_evaluation"] is None
    me = harness.client.get("/api/v1/me/recommendation", headers=STUDENT).json()
    assert me["recommendation"]["problem_slug"] == "count-occurrences"
    assert "upper_bound_confusion" not in str(me)

    # 2. The follow-up fails the same tests on count-occurrences. Its only equality model,
    # `upper_uses_strict`, prints 0 on every test, so since ADR-030 (rule 8a) it is not named:
    # the follow-up criterion is still checked on the tests, and the next step is a retry.
    _, trace = await harness.submit(
        source("count-occurrences", "error_models/upper_uses_strict.cpp"), "count-occurrences"
    )
    assert trace["diagnosis"]["outcome"] == "insufficient_evidence"
    assert trace["diagnosis"]["selected_model"] is None
    assert trace["diagnosis"]["rationale"]["rule"] == "8a"
    assert trace["diagnosis"]["rationale"]["consistent_model"] == "upper_uses_strict"
    ev = trace["followup_evaluation"]
    assert ev["verdict"] == "criterion_not_met"
    assert (ev["passed"], ev["failed"], ev["excluded"]) == (0, 9, 0)
    rec = trace["recommendation"]
    assert (rec["rule"], rec["action"], rec["problem_slug"]) == (
        "abstained",
        "retry",
        "count-occurrences",
    )
    assert rec["target_skills"] == [] and rec["criterion"] is None and rec["review_flag"]

    # 3. A correct retry: no criterion was recorded for a retry, so nothing is claimed.
    _, trace = await harness.submit(
        source("count-occurrences", "reference.cpp"), "count-occurrences"
    )
    assert trace["diagnosis"]["outcome"] == "no_failure_observed"
    assert trace["followup_evaluation"]["verdict"] == "not_comparable"
    assert trace["recommendation"]["problem_slug"] == "last-less-than"

    # 4. A correct follow-up on last-less-than meets the recorded criterion.
    _, trace = await harness.submit(source("last-less-than", "reference.cpp"), "last-less-than")
    assert trace["diagnosis"]["outcome"] == "no_failure_observed"
    ev = trace["followup_evaluation"]
    assert ev["verdict"] == "criterion_met"
    assert (ev["failed"], ev["excluded"]) == (0, 0)
    me = harness.client.get("/api/v1/me/recommendation", headers=STUDENT).json()
    assert me["last_followup"]["verdict"] == "criterion_met"
    assert me["recommendation"]["problem_slug"] in {
        "lower-bound",
        "count-occurrences",
        "first-true",
    }
