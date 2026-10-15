"""M2 acceptance: the demo content is diagnosable when executed in the sandbox."""

from codeadapt.content import load_catalogue
from codeadapt.content.fingerprint import fingerprint_problem
from codeadapt.content.validate import validate_fingerprints
from codeadapt.evidence import OutcomeKind
from codeadapt.execution import DockerSandbox
from tests.paths import DEMO_CONTENT


async def test_demo_catalogue_validates(sandbox: DockerSandbox) -> None:
    for problem in load_catalogue(DEMO_CONTENT):
        fps = await fingerprint_problem(sandbox, problem, repeats=2)
        report = validate_fingerprints(problem.spec, fps)
        assert report.ok, report.errors
        assert not report.warnings, report.warnings
        # Every pair of error models is separable by at least one test.
        assert all(p.distinguishing_tests for p in report.pairs)
        # Predictions are measured, not authored: the non-terminating model really times out.
        if problem.spec.slug == "lower-bound":
            loop = fps.models["no_progress_update"].tests["single_above"].signature
            assert loop is not None
            assert loop.kind is OutcomeKind.TIME_LIMIT
