"""Student-facing wording for recommendations and follow-up verdicts.

Allow-list rules as in feedback.py: the student sees the next problem, why in plain
words, and skill descriptions; never error-model keys, the ledger or the policy rationale.
Wording describes test outcomes and never claims learning ("mastered" is not a word here).
"""

from __future__ import annotations

from codeadapt.adaptation.models import Rule
from codeadapt.api.schemas import (
    FollowupVerdict,
    FollowupView,
    RecommendationAction,
    RecommendationView,
)
from codeadapt.content.catalogue import Catalogue
from codeadapt.db.models import FollowupEvaluationRow, RecommendationRow
from codeadapt.db.session import as_utc


def _title(catalogue: Catalogue, slug: str | None) -> str | None:
    problem = catalogue.by_slug.get(slug) if slug else None
    return problem.spec.title if problem else None


def recommendation_view(catalogue: Catalogue, row: RecommendationRow) -> RecommendationView:
    title = _title(catalogue, row.problem_slug) or "this problem"
    problem = catalogue.by_slug.get(row.problem_slug) if row.problem_slug else None
    focus = [
        problem.spec.skills[s] for s in row.target_skills if problem and s in problem.spec.skills
    ]
    rule = Rule(row.rule)
    action = RecommendationAction(row.action)
    if action is RecommendationAction.NONE:
        message = (
            "Every problem in this family has an attempt of yours with no failing tests. "
            "There is nothing further to recommend here yet."
        )
    elif rule is Rule.HYPOTHESIS_SUPPORTED and row.rationale.get("qualified_hypothesis"):
        message = (
            "Your last attempt failed in a pattern that has more than one possible cause. "
            f"{title} exercises the same idea."
        )
    elif rule is Rule.HYPOTHESIS_SUPPORTED:
        message = (
            f"Your last attempt behaved as if it had the specific error described in its "
            f"feedback. {title} exercises the same idea."
        )
    elif rule is Rule.AMBIGUOUS:
        message = (
            "Your last attempt failed tests in a way that fits more than one explanation. "
            f"{title} has tests that can tell those explanations apart."
        )
    elif rule is Rule.NO_FAILURE_OBSERVED:
        message = f"Your last attempt passed every test. Next, try {title}."
    elif rule is Rule.ABSTAINED:
        message = (
            "We could not draw a confident conclusion from your last attempt. "
            f"Use the test feedback and try {title} again."
        )
    else:
        message = (
            f"Your last attempt did not compile or could not be run. Fix it and resubmit {title}."
        )
    if action is RecommendationAction.RETRY and rule in (
        Rule.HYPOTHESIS_SUPPORTED,
        Rule.AMBIGUOUS,
        Rule.NO_FAILURE_OBSERVED,
    ):
        message += " It is the best match available, so it is the same problem again."
    return RecommendationView(
        action=action,
        problem_slug=row.problem_slug,
        problem_title=_title(catalogue, row.problem_slug),
        message=message,
        focus=focus,
        based_on_submission_id=row.submission_id,
        created_at=as_utc(row.created_at),
    )


def followup_view(
    catalogue: Catalogue, rec: RecommendationRow, row: FollowupEvaluationRow
) -> FollowupView:
    slug = rec.problem_slug or ""
    title = _title(catalogue, slug) or slug
    verdict = FollowupVerdict(row.verdict)
    total = row.passed + row.failed
    if verdict is FollowupVerdict.CRITERION_MET:
        message = (
            f"On {title}, your follow-up passed all {row.passed} tests related to the "
            "recommended focus. That is one passing attempt on these tests; it does not show "
            "the idea is fully learned, and later problems will check it in other settings."
        )
    elif verdict is FollowupVerdict.CRITERION_NOT_MET and row.failed:
        message = (
            f"On {title}, {row.failed} of {total} tests related to the recommended focus "
            "still failed."
        )
    elif verdict is FollowupVerdict.CRITERION_NOT_MET:
        message = f"On {title}, your follow-up still showed the error the recommendation targeted."
    else:
        message = f"Your follow-up on {title} could not be compared with the recommendation's goal."
    return FollowupView(
        verdict=verdict,
        problem_slug=slug,
        problem_title=title,
        message=message,
        submission_id=row.submission_id,
        created_at=as_utc(row.created_at),
    )
