import pytest

from codeadapt.evidence import OutcomeKind, Signature, signature_of
from codeadapt.evidence.signature import normalise_output
from codeadapt.execution.models import RunResult, RunStatus


def result(status: RunStatus, **kw: object) -> RunResult:
    base: dict[str, object] = {
        "status": status,
        "exit_code": 0,
        "signal": None,
        "stdout": "",
        "stdout_truncated": False,
        "stderr": "",
        "stderr_truncated": False,
        "wall_ms": 1,
        "oom_killed": False,
        "timed_out": False,
    }
    base.update(kw)
    return RunResult.model_validate(base)


@pytest.mark.parametrize(
    ("raw", "norm"),
    [
        ("2\n", "2"),
        ("2", "2"),
        ("2  \r\n\n\n", "2"),
        ("a b \nc\n", "a b\nc"),
        ("  lead\n", "  lead"),  # leading whitespace is significant
        ("", ""),
    ],
)
def test_normalise_output(raw: str, norm: str) -> None:
    assert normalise_output(raw) == norm


def test_signatures_by_status() -> None:
    assert signature_of(result(RunStatus.OK, stdout="3\n")) == Signature(
        kind=OutcomeKind.OUTPUT, detail="3"
    )
    assert str(signature_of(result(RunStatus.RUNTIME_ERROR, exit_code=139, signal=11))) == (
        "runtime_error:signal:11"
    )
    assert str(signature_of(result(RunStatus.RUNTIME_ERROR, exit_code=3))) == "runtime_error:exit:3"
    assert signature_of(result(RunStatus.TIME_LIMIT)).kind is OutcomeKind.TIME_LIMIT
    assert signature_of(result(RunStatus.MEMORY_LIMIT)).kind is OutcomeKind.MEMORY_LIMIT
    assert signature_of(result(RunStatus.OUTPUT_LIMIT, stdout="x" * 10)).detail == ""
    infra = signature_of(result(RunStatus.INFRASTRUCTURE_ERROR, detail="boom"))
    assert not infra.is_evidence
    assert signature_of(result(RunStatus.OK)).is_evidence


def test_signatures_are_hashable_and_comparable() -> None:
    a = Signature(kind=OutcomeKind.OUTPUT, detail="1")
    assert len({a, Signature(kind=OutcomeKind.OUTPUT, detail="1")}) == 1
    assert a != Signature(kind=OutcomeKind.OUTPUT, detail="2")
