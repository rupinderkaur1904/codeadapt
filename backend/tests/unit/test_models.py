import pytest
from pydantic import ValidationError

from codeadapt.execution.docker import _validate_sources
from codeadapt.execution.models import RunLimits, SourceFile


@pytest.mark.parametrize(
    "name", ["../etc/passwd", "/abs.cpp", "a b.cpp", "x.py", "$(rm).cpp", ".hidden.cpp", "a;b.cpp"]
)
def test_rejects_unsafe_file_names(name: str) -> None:
    with pytest.raises(ValidationError):
        SourceFile(name=name, content="")


@pytest.mark.parametrize("name", ["main.cpp", "harness.cc", "solution.hpp", "lib_1.h"])
def test_accepts_plain_file_names(name: str) -> None:
    assert SourceFile(name=name, content="").name == name


def test_validate_sources_limits() -> None:
    with pytest.raises(ValueError, match="at least one"):
        _validate_sources([])
    with pytest.raises(ValueError, match="duplicate"):
        _validate_sources(
            [SourceFile(name="a.cpp", content=""), SourceFile(name="a.cpp", content="")]
        )
    with pytest.raises(ValueError, match="translation unit"):
        _validate_sources([SourceFile(name="a.h", content="")])
    with pytest.raises(ValueError, match="exceed"):
        _validate_sources([SourceFile(name="a.cpp", content="x" * (256 * 1024 + 1))])
    units = _validate_sources(
        [SourceFile(name="a.cpp", content=""), SourceFile(name="b.h", content="")]
    )
    assert units == ["a.cpp"]


def test_run_limits_wall_includes_grace() -> None:
    assert RunLimits(cpu_seconds=2, startup_grace_seconds=1.5).wall_seconds == 3.5


def test_models_are_frozen_and_strict() -> None:
    with pytest.raises(ValidationError):
        RunLimits(cpu_seconds=0)
    with pytest.raises(ValidationError):
        SourceFile(name="a.cpp", content="", extra="no")  # type: ignore[call-arg]
