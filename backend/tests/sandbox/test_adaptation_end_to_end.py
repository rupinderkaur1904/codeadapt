"""M6 acceptance: diagnosis -> recommendation -> follow-up evaluation -> learner model.

A scripted synthetic learner (ADR-008) submits error-model mutants and references. This
checks the mechanism end to end; it is not evidence that the policy helps anyone learn.
"""

from __future__ import annotations

from typing import Any

from tests.paths import DEMO_CONTENT
from tests.sandbox.test_end_to_end import FIXTURES, RESEARCHER, STUDENT, Harness


def source(slug: str, file: str) -> str:
    return (DEMO_CONTENT / slug / file).read_text()


async def test_recommendation_and_followup_end_to_end(harness: Harness) -> None:
    # 0. A compile error first: not reliably evaluated, so it must not use up the counted
    # attempt on lower-bound (LM1, L1) and must give no skill observation.
    compile_view, trace = await harness.submit((FIXTURES / "compile_error.cpp").read_text())
    assert trace["diagnosis"]["outcome"] == "compile_error"
    rec = trace["recommendation"]
    assert (rec["action"], rec["problem_slug"], rec["criterion"]) == ("retry", "lower-bound", None)
    assert rec["target_skills"] == []

    # 1. A supported equality-handling error on lower-bound.
    named_view, trace = await harness.submit(
        source("lower-bound", "error_models/upper_bound_confusion.cpp")
    )
    assert trace["diagnosis"]["outcome"] == "hypothesis_supported"
    rec = trace["recommendation"]
    assert (rec["rule"], rec["action"], rec["problem_slug"]) == (
        "hypothesis_supported",
        "new_problem",
        "count-occurrences",
    )
    assert rec["target_skills"] == ["equality_handling"]
    # It follows the compile-error retry, which recorded no criterion: nothing is claimed.
    assert trace["followup_evaluation"]["verdict"] == "not_comparable"
    me = harness.client.get("/api/v1/me/recommendation", headers=STUDENT).json()
    assert me["recommendation"]["problem_slug"] == "count-occurrences"
    assert "upper_bound_confusion" not in str(me)

    # 2. The follow-up fails the same tests on count-occurrences. Its only equality model,
    # `upper_uses_strict`, prints 0 on every test, so since ADR-030 (rule 8a) it is not named:
    # the follow-up criterion is still checked on the tests, and the next step is a retry.
    abstained_view, trace = await harness.submit(
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
    retry_view, trace = await harness.submit(
        source("count-occurrences", "reference.cpp"), "count-occurrences"
    )
    assert trace["diagnosis"]["outcome"] == "no_failure_observed"
    assert trace["followup_evaluation"]["verdict"] == "not_comparable"
    assert trace["recommendation"]["problem_slug"] == "last-less-than"

    # 4. A correct follow-up on last-less-than meets the recorded criterion.
    correct_view, trace = await harness.submit(
        source("last-less-than", "reference.cpp"), "last-less-than"
    )
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

    # 5. The learner model (LM1, researcher-only) sees exactly the eligible evidence.
    assert (
        harness.client.get(
            "/api/v1/research/learner-model", params={"username": "dev-student"}, headers=STUDENT
        ).status_code
        == 403
    )
    r = harness.client.get(
        "/api/v1/research/learner-model", params={"username": "dev-student"}, headers=RESEARCHER
    )
    assert r.status_code == 200, r.text
    model = r.json()
    assert model["attempts"] == 5
    estimate = model["estimate"]
    assert estimate["parameter_set"] == "bkt-params-assumed-1"
    assert estimate["label"] == "estimated under assumed parameters"
    traced = [(s["skill"], t) for s in estimate["skills"] for t in s["observations"]]
    by_submission: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for skill, t in traced:
        by_submission.setdefault(t["observation"]["submission_id"], []).append((skill, t))

    # The compile error gives nothing; the named diagnosis is the only incorrect observation,
    # on the model's skill, and it is counted although a compile error came first.
    assert compile_view["id"] not in by_submission
    incorrect = [(skill, t) for skill, t in traced if t["observation"]["value"] == "incorrect"]
    assert [(skill, t["observation"]["submission_id"]) for skill, t in incorrect] == [
        ("equality_handling", named_view["id"])
    ]
    assert incorrect[0][1]["counted"] is True
    assert incorrect[0][1]["observation"]["basis"] == "supported diagnosis: upper_bound_confusion"
    # The abstention (rule 8a) gives no negative evidence and nothing on the skill of its
    # consistent model. It still used up the counted attempt (feedback was delivered).
    abstained = by_submission.get(abstained_view["id"], [])
    assert all(t["observation"]["value"] == "correct" and t["counted"] for _, t in abstained)
    assert "equality_handling" not in {skill for skill, _ in abstained}
    # Known limitation, pinned so it stays visible (docs/limitations.md): rule C gives
    # positive evidence to a skill whose every probing test passed, so this program, which
    # prints 0 on every test, earns `problem_specification` = correct from the absent-target
    # tests.
    assert {skill for skill, _ in abstained} == {"problem_specification"}
    # The correct retry on count-occurrences is visible but not counted.
    retry = by_submission[retry_view["id"]]
    assert retry and all(not t["counted"] and t["reason"].startswith("retry") for _, t in retry)
    # The correct follow-up is counted as positive evidence.
    follow = by_submission[correct_view["id"]]
    assert follow and all(
        t["counted"] and t["observation"]["value"] == "correct" for _, t in follow
    )
    # Display threshold: no estimate below 3 counted observations from 2 problems.
    for s in estimate["skills"]:
        enough = s["counted"] >= 3 and s["distinct_problems"] >= 2
        assert (s["state"] == "estimated") == enough
        assert (s["p_known"] is not None) == enough
    # Students never see learner-model output.
    me = harness.client.get("/api/v1/me/recommendation", headers=STUDENT).json()
    assert "p_known" not in str(me) and "assumed parameters" not in str(me)


async def test_non_unique_min_capacity_attribution_end_to_end(harness: Harness) -> None:
    # Owner decision 2026-10-25 (option b, L20): `strict_day_limit` is still diagnosed and
    # traced, shown to the student as one possible cause, and adds no equality_handling
    # evidence or BKT update.
    view, trace = await harness.submit(
        source("min-capacity", "error_models/strict_day_limit.cpp"), "min-capacity"
    )
    diagnosis = trace["diagnosis"]
    assert diagnosis["outcome"] == "hypothesis_supported"
    assert diagnosis["selected_model"] == "strict_day_limit"
    # Unqualified by the method itself (several behaviour groups); the trace keeps it all.
    assert diagnosis["rationale"]["evidence_strength"] == "multiple"
    assert "not proof" in diagnosis["rationale"]["caveat"]
    assert trace["observations"]

    feedback = view["feedback"]
    assert "other mistakes can produce the same pattern" in feedback["message"]
    assert "exactly the allowed number of days" in feedback["hint"]
    assert "strict_day_limit" not in str(view)

    rec = trace["recommendation"]
    assert rec["rule"] == "hypothesis_supported"
    assert rec["target_skills"] == ["equality_handling"]
    assert rec["rationale"]["qualified_hypothesis"] is True

    r = harness.client.get(
        "/api/v1/research/learner-model", params={"username": "dev-student"}, headers=RESEARCHER
    )
    assert r.status_code == 200, r.text
    skills = {s["skill"]: s for s in r.json()["estimate"]["skills"]}
    assert "equality_handling" not in skills
    values = [t["observation"]["value"] for s in skills.values() for t in s["observations"]]
    assert "incorrect" not in values
