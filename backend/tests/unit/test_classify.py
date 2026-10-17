import pytest

from codeadapt.execution.classify import RawOutcome, classify_compile, classify_run, signal_of
from codeadapt.execution.models import CompileStatus, RunStatus


def raw(**kw: object) -> RawOutcome:
    base: dict[str, object] = {
        "started": True,
        "exit_code": 0,
        "oom_killed": False,
        "timed_out": False,
        "output_overflow": False,
    }
    base.update(kw)
    return RawOutcome(**base)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        (raw(), RunStatus.OK),
        (raw(exit_code=1), RunStatus.RUNTIME_ERROR),
        (raw(exit_code=139), RunStatus.RUNTIME_ERROR),  # SIGSEGV
        (raw(exit_code=152), RunStatus.TIME_LIMIT),  # SIGXCPU from the CPU rlimit
        # Wall deadline without the CPU limit: a stalled host looks the same (ADR-023).
        (raw(exit_code=137, timed_out=True), RunStatus.INCONCLUSIVE),
        (raw(exit_code=None, timed_out=True), RunStatus.INCONCLUSIVE),
        # The CPU limit decides even if the wall deadline also fired.
        (raw(exit_code=152, timed_out=True), RunStatus.TIME_LIMIT),
        (raw(exit_code=137, oom_killed=True), RunStatus.MEMORY_LIMIT),
        (raw(exit_code=137, output_overflow=True), RunStatus.OUTPUT_LIMIT),
        (raw(started=False, exit_code=None), RunStatus.INFRASTRUCTURE_ERROR),
        (raw(exit_code=None), RunStatus.INFRASTRUCTURE_ERROR),
        # The client's streams disagree with the container: the output is not evidence.
        (raw(stream_mismatch=True), RunStatus.INFRASTRUCTURE_ERROR),
        (raw(output_incomplete=True), RunStatus.INFRASTRUCTURE_ERROR),
        # Memory beats a later timeout: OOM explains why the program stopped making progress.
        (raw(exit_code=137, oom_killed=True, timed_out=True), RunStatus.MEMORY_LIMIT),
    ],
)
def test_classify_run(outcome: RawOutcome, expected: RunStatus) -> None:
    assert classify_run(outcome) is expected


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        (raw(), CompileStatus.OK),
        (raw(exit_code=1), CompileStatus.ERROR),
        (raw(exit_code=137), CompileStatus.TIME_LIMIT),  # CPU hard limit
        (raw(exit_code=137, oom_killed=True), CompileStatus.MEMORY_LIMIT),
        (raw(exit_code=1, timed_out=True), CompileStatus.TIME_LIMIT),
        (raw(started=False, exit_code=None), CompileStatus.INFRASTRUCTURE_ERROR),
        (raw(stream_mismatch=True), CompileStatus.INFRASTRUCTURE_ERROR),
    ],
)
def test_classify_compile(outcome: RawOutcome, expected: CompileStatus) -> None:
    assert classify_compile(outcome) is expected


@pytest.mark.parametrize(
    ("code", "sig"),
    [(None, None), (0, None), (1, None), (128, None), (137, 9), (139, 11), (300, None)],
)
def test_signal_of(code: int | None, sig: int | None) -> None:
    assert signal_of(code) == sig
