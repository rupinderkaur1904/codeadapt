"""Student evidence collection re-measures infrastructure errors, never program behaviour."""

from codeadapt.evidence.collect import INFRA_ATTEMPTS, collect_evidence
from codeadapt.evidence.signature import signature_of
from codeadapt.execution.models import RunStatus
from tests.unit.content.test_fingerprint import PROBLEM, ScriptedJob, ScriptedSandbox, result

INFRA = result(RunStatus.INFRASTRUCTURE_ERROR)
REFERENCE = {t.key: signature_of(result(RunStatus.OK, "1")) for t in PROBLEM.spec.tests}


async def test_transient_infrastructure_error_is_measured_again() -> None:
    first = PROBLEM.spec.tests[0]
    job = ScriptedJob({first.input: [INFRA, result(RunStatus.OK, "1")]})
    evidence = await collect_evidence(ScriptedSandbox(job), PROBLEM, "", REFERENCE)  # type: ignore[arg-type]
    assert evidence.standard[first.key].status is RunStatus.OK
    assert first.key not in evidence.repeats  # it matched the reference after the retry


async def test_persistent_infrastructure_error_stays_an_infrastructure_error() -> None:
    first = PROBLEM.spec.tests[0]
    job = ScriptedJob({first.input: [INFRA] * (2 * INFRA_ATTEMPTS)})
    evidence = await collect_evidence(ScriptedSandbox(job), PROBLEM, "", REFERENCE)  # type: ignore[arg-type]
    assert evidence.standard[first.key].status is RunStatus.INFRASTRUCTURE_ERROR
    assert not signature_of(evidence.standard[first.key]).is_evidence


async def test_program_behaviour_is_not_retried() -> None:
    first = PROBLEM.spec.tests[0]
    wrong = result(RunStatus.OK, "5")
    job = ScriptedJob({first.input: [wrong, result(RunStatus.OK, "1")]})
    evidence = await collect_evidence(ScriptedSandbox(job), PROBLEM, "", REFERENCE)  # type: ignore[arg-type]
    # The wrong output is kept; the reliability repeat run is what sees "1".
    assert evidence.standard[first.key].stdout == "5"
    assert [r.stdout for r in evidence.repeats[first.key]] == ["1"]
    assert evidence.observations()[0].excluded_reason is not None
