"""D1 technique-evidence eligibility (P-D1a, owner approval 2026-10-26; ADR-035).

A problem that forbids named library calls lists them in `banned_names`. An attempt whose
source names one still runs, is still diagnosed and still counts in attempt statistics, but it
gives no skill observations. Rule C, the diagnosis rules and the recommendation policy are
unchanged. Detection is a static token match: it does not show which algorithm the program
uses or what its complexity is.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from codeadapt.adaptation import SkillMap, build_ledger, skill_observations
from codeadapt.adaptation.technique import banned_names_found, strip_comments_and_literals
from codeadapt.content.loader import ContentError, load_problem, statement_bans
from codeadapt.db.models import DiagnosisRow, Submission, utcnow
from codeadapt.diagnosis import Outcome
from codeadapt.learner.bkt import counted_attempts, estimate
from codeadapt.worker.adapt import attempt_record
from tests.paths import DEMO_CONTENT
from tests.unit.test_adaptation import POLICY, PROBLEMS, attempt

LB_BANNED = PROBLEMS["lower-bound"].banned_names
SQRT_BANNED = PROBLEMS["integer-sqrt"].banned_names

HAND_WRITTEN = """
#include <vector>
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = (int)a.size();
    while (lo < hi) { int mid = lo + (hi - lo) / 2; if (a[mid] < target) lo = mid + 1; else hi = mid; }
    return lo;
}
"""


# ---------------------------------------------------------------------- the detector
@pytest.mark.parametrize(
    ("source", "found"),
    [
        ("return std::lower_bound(a.begin(), a.end(), t) - a.begin();", ("std::lower_bound",)),
        ("return std :: upper_bound (a.begin(), a.end(), t) - a.begin();", ("std::upper_bound",)),
        (
            "using namespace std; return lower_bound(a.begin(), a.end(), t) - a.begin();",
            ("std::lower_bound",),
        ),
        ("return std::ranges::lower_bound(a, t) - a.begin();", ("std::lower_bound",)),
        (
            "using namespace std; return ranges::equal_range(a, t).begin() - a.begin();",
            ("std::equal_range",),
        ),
        ("using std::partition_point;", ("std::partition_point",)),
        ("auto f = &std::lower_bound<It, int>;", ("std::lower_bound",)),
        ("return lower_bound<It, int>(a.begin(), a.end(), t) - a.begin();", ("std::lower_bound",)),
        (
            "auto x = std::lower_bound(b, e, t); auto y = std::upper_bound(b, e, t);",
            ("std::lower_bound", "std::upper_bound"),
        ),
    ],
)
def test_banned_lower_bound_names_are_found(source: str, found: tuple[str, ...]) -> None:
    assert banned_names_found(source, LB_BANNED) == found


@pytest.mark.parametrize(
    "source",
    [
        HAND_WRITTEN,
        "// std::lower_bound would be O(log n) too\n" + HAND_WRITTEN,
        "/* do not use std::lower_bound(a.begin(), a.end(), t) */" + HAND_WRITTEN,
        'const char* s = "std::lower_bound(";' + HAND_WRITTEN,
        'auto s = R"x(lower_bound(a, t))x";' + HAND_WRITTEN,
        "char c = '('; int lower_bound_count = 0;" + HAND_WRITTEN,
        "s.lower_bound(t); p->upper_bound(t); m.equal_range(t);",  # member functions
        "mine::lower_bound(a, t);",  # another namespace
        "int lower_bound(const std::vector<int>& a, int t) { return 0; }\n"
        "int f(const std::vector<int>& a) { return lower_bound(a, 3); }",  # the student's own
        "int my_lower_bound(int x); int lower_boundary = 2;",
        # The student's own lambda or function object of that name (2026-10-26 audit).
        "auto lower_bound = [&](int t) { return 0; }; return lower_bound(3);",
        "std::function<int(int)> lower_bound = f; return lower_bound(3);",
    ],
)
def test_names_that_are_not_a_banned_call_are_not_found(source: str) -> None:
    assert banned_names_found(source, LB_BANNED) == ()


def test_c_library_bans_cover_qualified_and_unqualified_calls() -> None:
    assert banned_names_found("return (long long)std::sqrt((double)x);", SQRT_BANNED) == ("sqrt",)
    assert banned_names_found("return (long long)sqrt(x);", SQRT_BANNED) == ("sqrt",)
    assert banned_names_found("return std::pow(x, 0.5);", SQRT_BANNED) == ("pow",)
    assert banned_names_found("return sqrtl(x);", SQRT_BANNED) == ("sqrtl",)
    # isqrt, a hand-written helper, and a variable named sqrt_guess are not the C library call.
    assert (
        banned_names_found("long long isqrt(long long x); long long sqrt_guess = 1;", SQRT_BANNED)
        == ()
    )
    assert (
        banned_names_found("long long r = 0; while ((r + 1) * (r + 1) <= x) ++r;", SQRT_BANNED)
        == ()
    )
    # A lambda named after a banned function is the student's own (2026-10-26 audit).
    square = "auto pow = [](long long v) { return v * v; }; while (pow(r + 1) <= x) ++r;"
    assert banned_names_found(square, SQRT_BANNED) == ()
    # A comparison is not an initialiser: the qualified name is still found.
    assert banned_names_found("bool b = std::pow == nullptr;", SQRT_BANNED) == ("pow",)


def test_stripping_keeps_code_and_removes_comments_and_literals() -> None:
    code = strip_comments_and_literals("int a = 1; // x\nauto s = \"y\"; /* z */ char c = 'w';")
    assert "int a = 1;" in code and "auto s =" in code
    assert not {"x", "y", "z", "w"} & set(code.split())


def test_a_problem_without_bans_finds_nothing() -> None:
    assert PROBLEMS["stock-profit"].banned_names == ()
    assert banned_names_found("std::lower_bound(b, e, t);", ()) == ()


# ---------------------------------------------------------------------- versioned metadata
def test_banned_names_match_every_statement() -> None:
    with_bans = {slug for slug, spec in PROBLEMS.items() if spec.banned_names}
    assert len(with_bans) == 14
    assert {"dedup-sorted", "first-max-index"} < with_bans
    for spec in PROBLEMS.values():
        assert SkillMap.from_spec(spec, "v").banned_names == tuple(sorted(spec.banned_names))


def test_statement_parsing_flattens_line_breaks() -> None:
    text = "Do not call `std::lower_bound`,\n`std::upper_bound` or `x`. Do call `y`."
    assert statement_bans(text) == {"std::lower_bound", "std::upper_bound", "x"}


@pytest.mark.parametrize("bad", ["std::", "lower bound", "std::vector<int>", "boost::find", "1x"])
def test_invalid_banned_names_are_rejected(bad: str) -> None:
    data = PROBLEMS["lower-bound"].model_dump()
    with pytest.raises(ValidationError, match="invalid banned name"):
        type(PROBLEMS["lower-bound"]).model_validate({**data, "banned_names": [bad]})


def test_duplicate_banned_names_are_rejected() -> None:
    data = PROBLEMS["lower-bound"].model_dump()
    with pytest.raises(ValidationError, match="duplicate banned name"):
        type(PROBLEMS["lower-bound"]).model_validate(
            {**data, "banned_names": ["std::lower_bound", "std::lower_bound"]}
        )


def test_the_loader_rejects_a_list_that_differs_from_the_statement(tmp_path: Path) -> None:
    content = tmp_path / "lower-bound"
    shutil.copytree(DEMO_CONTENT / "lower-bound", content)
    toml = content / "problem.toml"
    text = toml.read_text()
    toml.write_text(text.replace('"std::equal_range", ', "", 1))
    with pytest.raises(ContentError, match="banned_names"):
        load_problem(content)


# ---------------------------------------------------------------------- evidence eligibility
def lb(outcome: Outcome, n: int = 0, banned: tuple[str, ...] = (), **kw):  # type: ignore[no-untyped-def]
    return attempt("lower-bound", outcome, n=n, **kw).model_copy(
        update={"banned_names_found": banned}
    )


def test_a_passing_attempt_with_a_banned_call_gives_no_observations() -> None:
    clean = lb(Outcome.NO_FAILURE_OBSERVED)
    assert {o.value for o in skill_observations([clean], PROBLEMS)} == {"correct"}
    banned = lb(Outcome.NO_FAILURE_OBSERVED, banned=("std::lower_bound",))
    assert skill_observations([banned], PROBLEMS) == ()
    assert not estimate([banned], PROBLEMS).skills


def test_a_failing_attempt_with_a_banned_call_gives_no_observations() -> None:
    failing = ("sample_present", "equal_first", "equal_last", "duplicates_middle")
    banned = lb(
        Outcome.HYPOTHESIS_SUPPORTED,
        model="upper_bound_confusion",
        failing=failing,
        banned=("std::upper_bound",),
    )
    assert skill_observations([banned], PROBLEMS) == ()


def test_an_attempt_without_a_banned_call_keeps_its_evidence() -> None:
    # A submission that fails for an unrelated reason (a named equality error) is unaffected.
    a = lb(
        Outcome.HYPOTHESIS_SUPPORTED,
        model="stops_at_first_match",
        failing=("duplicates_middle", "duplicates_all"),
    )
    assert ("equality_handling", "incorrect") in {
        (o.skill, o.value) for o in skill_observations([a], PROBLEMS)
    }


def test_the_attempt_still_exists_for_the_ledger_policy_and_counting() -> None:
    banned = lb(Outcome.NO_FAILURE_OBSERVED, n=0, banned=("std::lower_bound",))
    later = lb(Outcome.NO_FAILURE_OBSERVED, n=1)
    # The policy's ledger and recommendation are unchanged by the flag.
    assert build_ledger([banned], PROBLEMS) == build_ledger(
        [banned.model_copy(update={"banned_names_found": ()})], PROBLEMS
    )
    assert POLICY.recommend(banned, [banned], PROBLEMS) == POLICY.recommend(
        banned.model_copy(update={"banned_names_found": ()}),
        [banned.model_copy(update={"banned_names_found": ()})],
        PROBLEMS,
    )
    # Like an abstention, it was reliably evaluated, so it uses the counted opportunity: a
    # retry on the same version stays uncounted (documented in ADR-035 as a decision to review).
    assert counted_attempts([banned, later]) == {banned.submission_id}
    obs = skill_observations([banned, later], PROBLEMS)
    assert obs and {o.submission_id for o in obs} == {later.submission_id}
    assert all(not s.counted for s in estimate([banned, later], PROBLEMS).skills)


def test_attempt_record_looks_up_the_versions_own_banned_names() -> None:
    spec = PROBLEMS["lower-bound"]
    sub = Submission(
        id="s1",
        user_id=1,
        problem_version="v",
        source="#include <algorithm>\nusing namespace std;\nint f(){ return lower_bound(b,e,t)-b; }",
        source_sha256="0" * 64,
        origin="student",
        data_class="dev",
        created_at=utcnow(),
    )
    diag = DiagnosisRow(outcome="no_failure_observed", candidates=[], rationale={})
    current = SkillMap.from_spec(spec, "v")
    assert attempt_record(sub, "lower-bound", diag, current).banned_names_found == (
        "std::lower_bound",
    )
    # A snapshot stored before this change has no banned names: the attempt keeps its evidence.
    old = current.model_copy(update={"banned_names": ()})
    assert attempt_record(sub, "lower-bound", diag, old).banned_names_found == ()
    assert attempt_record(sub, "lower-bound", diag, None).banned_names_found == ()
    stored = current.model_dump(mode="json")
    del stored["banned_names"]
    assert SkillMap.from_stored(stored) == old
