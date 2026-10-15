import pytest

from codeadapt.evidence.reliability import STUDENT_PHRASES, assess, sanitizer_finding
from codeadapt.execution.models import RunResult, RunStatus

ASAN = """=================================================================
==7==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x502 at pc 0x4 bp 0x7
READ of size 4 at 0x502 thread T0
"""
UBSAN = "solution.cpp:7:34: runtime error: signed integer overflow: 2147483647 + 5 cannot be represented in type 'int'\n"
NULL_REF = "stl_vector.h:1150:34: runtime error: reference binding to null pointer of type 'const value_type'\n"
LEAK = "==9==ERROR: LeakSanitizer: detected memory leaks\n"


def run(stdout: str = "1\n", stderr: str = "", status: RunStatus = RunStatus.OK) -> RunResult:
    return RunResult(
        status=status,
        exit_code=0 if status is RunStatus.OK else 1,
        signal=None,
        stdout=stdout,
        stdout_truncated=False,
        stderr=stderr,
        stderr_truncated=False,
        wall_ms=1,
        oom_killed=False,
        timed_out=False,
    )


@pytest.mark.parametrize(
    ("stderr", "tool", "kind"),
    [
        (ASAN, "asan", "heap-buffer-overflow"),
        (UBSAN, "ubsan", "signed-integer-overflow"),
        (NULL_REF, "ubsan", "null-pointer"),
        (
            "x: runtime error: index 5 out of bounds for type 'int [4]'",
            "ubsan",
            "index-out-of-bounds",
        ),
        ("x: runtime error: something new", "ubsan", "undefined-behaviour"),
    ],
)
def test_sanitizer_finding(stderr: str, tool: str, kind: str) -> None:
    finding = sanitizer_finding(stderr)
    assert finding is not None
    assert (finding.tool, finding.kind) == (tool, kind)


@pytest.mark.parametrize("stderr", ["", LEAK, "my own debug output\n", "error: something"])
def test_no_finding(stderr: str) -> None:
    assert sanitizer_finding(stderr) is None


def test_every_known_asan_kind_has_student_phrase() -> None:
    for kind in ("heap-buffer-overflow", "signed-integer-overflow", "null-pointer"):
        assert kind in STUDENT_PHRASES


def test_assess_marks_sanitizer_and_nondeterminism() -> None:
    standard = {"a": run("1\n"), "b": run("2\n"), "c": run("3\n"), "d": run("4\n")}
    repeats = {"b": [run("9\n")], "c": [run("3\n")]}
    sanitized = {
        "a": run(stderr=ASAN, status=RunStatus.RUNTIME_ERROR),
        "b": run(),
        "c": run(),
        "d": run(),
    }
    result = assess(standard, repeats, sanitized)
    assert result["a"].excluded_reason == "sanitizer: heap-buffer-overflow"
    assert result["b"].excluded_reason is not None
    assert result["b"].excluded_reason.startswith("non-deterministic")
    assert result["c"].excluded_reason is None  # repeat agreed
    assert result["d"].excluded_reason is None


def test_sanitizer_takes_precedence_and_absence_is_tolerated() -> None:
    standard = {"a": run("1\n")}
    both = assess(standard, {"a": [run("2\n")]}, {"a": run(stderr=UBSAN)})
    assert both["a"].excluded_reason == "sanitizer: signed-integer-overflow"
    unavailable = assess(standard, {}, None)
    assert unavailable["a"].excluded_reason is None
    assert unavailable["a"].finding is None
