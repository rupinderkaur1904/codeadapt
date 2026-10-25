"""Family-level pipeline coverage (owner action 4, 2026-10-25).

For one problem of each of the five families, held-out programs go through the API, the
worker pipeline, the Docker sandbox, diagnosis, the evidence ledger and the recommendation
policy: a correct program, a modelled bug that is named, an unmodelled bug, and, where the
family has one, a diagnosis that is reported as qualified. The researcher's learner-model view
must then hold exactly one `incorrect` observation per unqualified named diagnosis, on the
model's skill, and none from the qualified or abstaining attempts.

The programs are synthetic and author-written (eval/heldout). This checks the mechanism
for every family; it says nothing about diagnostic accuracy on real code.

An `ambiguous` outcome cannot be produced here: content validation rejects two error models
with identical fingerprints, so on valid content two models can only both stay consistent
when some tests are excluded as unreliable, which is not deterministic. Its evidence rule is
covered in tests/unit/test_learner_model.py.

Runtime: about 5 minutes under runc locally (fingerprints are measured once per problem);
it runs as its own CI shard, `families`, under runc and gVisor.
"""

from __future__ import annotations

import tomllib
from typing import Any

import pytest

from tests.paths import DEMO_CONTENT, HELDOUT
from tests.sandbox.test_end_to_end import RESEARCHER, STUDENT, Harness

NOTHING_TO_RECOMMEND = (
    "There is no further problem to recommend here yet. You can choose any problem from the list."
)

# (family, problem, [(held-out file, expected kind)]). Kinds: correct, named, qualified,
# unmodelled. The files are the first held-out case of each kind, except where a family's
# qualified case is added.
FAMILIES = [
    (
        "binary-search",
        "last-less-than",
        [
            ("closed_interval_correct.cpp", "correct"),
            ("closed_interval_le.cpp", "named"),
            # hi_init_last_index: one behaviour group, so the method itself qualifies it.
            ("closed_from_last_index.cpp", "qualified"),
            ("le_and_clamped.cpp", "unmodelled"),
        ],
    ),
    (
        "arrays",
        "stock-profit",
        [
            ("suffix_max.cpp", "correct"),
            ("must_trade.cpp", "named"),
            # ignores_order: a documented known_limitation (ADR-032 route).
            ("sorted_spread.cpp", "qualified"),
            ("consecutive_days.cpp", "unmodelled"),
        ],
    ),
    (
        "two-pointers",
        "dedup-sorted",
        [
            ("write_index_loop.cpp", "correct"),
            ("reads_to_n_minus_one.cpp", "named"),
            ("keeps_two_copies.cpp", "unmodelled"),
        ],
    ),
    (
        "sliding-window",
        "distinct-in-windows",
        [
            ("distinct_counter.cpp", "correct"),
            ("counter_never_drops.cpp", "named"),
            ("runs_in_window.cpp", "unmodelled"),
        ],
    ),
    (
        "prefix-sums",
        "range-sum-queries",
        [
            ("one_based_prefix_ll.cpp", "correct"),
            ("inclusive_stops_short.cpp", "named"),
            ("drops_left_end.cpp", "unmodelled"),
        ],
    ),
]


def truth(slug: str, file: str) -> str:
    cases = tomllib.loads((HELDOUT / slug / "cases.toml").read_text())["cases"]
    (case,) = [c for c in cases if c["file"] == file]
    return str(case["truth"])


def spec(slug: str) -> dict[str, Any]:
    return tomllib.loads((DEMO_CONTENT / slug / "problem.toml").read_text())


@pytest.mark.parametrize(("family", "slug", "programs"), FAMILIES, ids=[f[0] for f in FAMILIES])
async def test_family_pipeline_end_to_end(
    harness: Harness, family: str, slug: str, programs: list[tuple[str, str]]
) -> None:
    problem = spec(slug)
    assert problem["family"] == family
    skills = {m["key"]: m["skill"] for m in problem["error_models"]}
    recommendable = {
        p.spec.slug
        for p in harness.catalogue.problems
        if p.spec.family == family and p.spec.recommendable
    }

    expected_incorrect: list[tuple[str, str]] = []
    no_negative: list[str] = []
    for file, kind in programs:
        source = (HELDOUT / slug / file).read_text()
        view, trace = await harness.submit(source, slug)
        assert view["status"] == "completed", (file, view)
        diagnosis, rec = trace["diagnosis"], trace["recommendation"]
        outcome = diagnosis["outcome"]
        if kind == "correct":
            assert outcome == "no_failure_observed", (file, diagnosis)
            if recommendable - {slug}:
                assert rec["action"] == "new_problem" and rec["problem_slug"] in recommendable
            else:
                # Nothing recommendable is left in the family (L21): no claim that every
                # problem was passed.
                assert rec["action"] == "none", rec
                me = harness.client.get("/api/v1/me/recommendation", headers=STUDENT).json()
                assert me["recommendation"]["message"] == NOTHING_TO_RECOMMEND
        elif kind == "named":
            model = truth(slug, file)
            assert outcome == "hypothesis_supported", (file, diagnosis)
            assert diagnosis["selected_model"] == model
            assert diagnosis["rationale"]["evidence_strength"] == "multiple"
            assert rec["rule"] == "hypothesis_supported"
            assert rec["target_skills"] == [skills[model]]
            assert rec["rationale"].get("qualified_hypothesis") is not True
            expected_incorrect.append((skills[model], view["id"]))
        elif kind == "qualified":
            model = truth(slug, file)
            assert outcome == "hypothesis_supported", (file, diagnosis)
            assert diagnosis["selected_model"] == model
            assert rec["rationale"]["qualified_hypothesis"] is True
            no_negative.append(view["id"])
        else:
            assert outcome == "unmodelled_behaviour", (file, diagnosis)
            assert diagnosis["selected_model"] is None
            assert (rec["action"], rec["problem_slug"]) == ("retry", slug)
            assert rec["target_skills"] == []
            no_negative.append(view["id"])
        # Students never see model keys.
        assert not any(key in str(view) for key in skills)

    r = harness.client.get(
        "/api/v1/research/learner-model", params={"username": "dev-student"}, headers=RESEARCHER
    )
    assert r.status_code == 200, r.text
    estimate = r.json()["estimate"]
    assert estimate["label"] == "estimated under assumed parameters"
    traced = [(s["skill"], t["observation"]) for s in estimate["skills"] for t in s["observations"]]
    incorrect = sorted(
        (skill, o["submission_id"]) for skill, o in traced if o["value"] == "incorrect"
    )
    # Exactly the unqualified named diagnoses give negative evidence, on the model's skill.
    assert incorrect == sorted(expected_incorrect)
    assert not {o["submission_id"] for _, o in traced if o["value"] == "incorrect"} & set(
        no_negative
    )
    # Every observed skill is one the problem declares (ADR-033 keys for the new families).
    assert {skill for skill, _ in traced} <= set(problem["skills"])
    # The student-facing recommendation never shows learner-model output.
    me = harness.client.get("/api/v1/me/recommendation", headers=STUDENT).json()
    assert "p_known" not in str(me) and "assumed parameters" not in str(me)
