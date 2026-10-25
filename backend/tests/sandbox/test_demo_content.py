"""M2 acceptance: the demo content is diagnosable when executed in the sandbox.

CE0: every declared `distinguishes` agrees with the measurement (a mismatch is an error),
and every weakness is a documented single-behaviour model. For the original four problems that
is exactly `hi_init_last_index`; every newer problem's weak models must each carry a
`known_limitation`, and no undocumented weakness is allowed.

A `known_limitation` on a model that is *not* weak is allowed only where it is listed in
NON_UNIQUE_ATTRIBUTION: a multi-group model whose skill attribution is documented as not unique
(L20; ADR-032 and the bank expansion). Its diagnoses are qualified and add no negative evidence.
"""

from codeadapt.content import load_catalogue
from codeadapt.content.fingerprint import fingerprint_problem
from codeadapt.content.validate import validate_fingerprints
from codeadapt.evidence import OutcomeKind
from codeadapt.execution import DockerSandbox
from tests.paths import DEMO_CONTENT, ORIGINAL_SLUGS

NON_UNIQUE_ATTRIBUTION = {
    "min-capacity": {"strict_day_limit", "full_day_overflows"},
    "stock-profit": {"ignores_order"},
}


async def test_demo_catalogue_validates(sandbox: DockerSandbox) -> None:
    for problem in load_catalogue(DEMO_CONTENT):
        fps = await fingerprint_problem(sandbox, problem, repeats=2)
        report = validate_fingerprints(problem.spec, fps)
        assert report.ok, report.errors
        assert not report.warnings, report.warnings
        weak = {m.key for m in report.models if m.behaviour_groups < 2}
        documented = {m.key for m in problem.spec.error_models if m.known_limitation}
        non_unique = NON_UNIQUE_ATTRIBUTION.get(problem.spec.slug, set())
        assert weak == documented - non_unique, (problem.spec.slug, weak, documented)
        # The non-unique ones really span several behaviour groups (they are not weak).
        assert non_unique <= documented and not non_unique & weak, (problem.spec.slug, weak)
        assert len(report.limitations) == len(weak)
        if problem.spec.slug in ORIGINAL_SLUGS:
            assert weak == {"hi_init_last_index"}, weak
        # Every pair of error models is separable by at least one test.
        assert all(p.distinguishing_tests for p in report.pairs)
        # Predictions are measured, not authored: the non-terminating model really times out.
        if problem.spec.slug == "lower-bound":
            loop = fps.models["no_progress_update"].tests["single_above"].signature
            assert loop is not None
            assert loop.kind is OutcomeKind.TIME_LIMIT
