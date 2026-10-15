"""M7 acceptance: the evaluation harness runs the held-out set and is reproducible.

Synthetic cases (ADR-008). This checks that the harness measures and reports; the numbers
it produces are not claims about real students.
"""

from __future__ import annotations

from codeadapt.content.catalogue import Catalogue
from codeadapt.diagnosis import FingerprintConsistencyV1
from codeadapt.evaluation.heldout import load_heldout
from codeadapt.evaluation.runner import evaluate, render_markdown
from codeadapt.execution import DockerSandbox
from tests.paths import DEMO_CONTENT, HELDOUT


async def test_lower_bound_heldout_evaluation_is_reproducible(sandbox: DockerSandbox) -> None:
    catalogue = Catalogue.load(DEMO_CONTENT)
    cases = load_heldout(HELDOUT, {"lower-bound"})
    report = await evaluate(sandbox, catalogue, cases, FingerprintConsistencyV1(), runs=2)
    (problem,) = report.problems
    rows = {c.file: c for c in problem.cases}
    assert set(rows) == {c.file for c in cases}
    # Every case produced the same evidence and diagnosis on both runs.
    assert problem.metrics.reproducibility.numerator == len(cases)
    # Facts about specific cases, established by running them (also covered in M3 tests).
    assert rows["upper_bound_closed.cpp"].classification == "true_diagnosis"
    assert rows["correct_iterative.cpp"].classification == "correct_pass"
    assert rows["double_bug.cpp"].outcome == "unmodelled_behaviour"
    markdown = render_markdown(report)
    assert "## Limitations" in markdown
    assert "not evidence that CodeAdapt helps anyone learn" in markdown
