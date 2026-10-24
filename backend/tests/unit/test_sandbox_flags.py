"""Container flags per runtime (runc vs gVisor), without a docker daemon."""

from codeadapt.execution.docker import (
    RUNSC_HOST_PIDS_HEADROOM,
    DockerSandbox,
    DockerSandboxConfig,
)

LIMITS = {"memory_mib": 256, "pids": 16, "open_files": 64, "cpu_seconds": 2, "fsize": 0}


def _value(args: list[str], flag: str) -> list[str]:
    return [args[i + 1] for i, a in enumerate(args) if a == flag]


def test_runc_flags_are_unchanged() -> None:
    args = DockerSandbox(DockerSandboxConfig())._hardening(**LIMITS)
    assert _value(args, "--pids-limit") == ["16"]
    assert not any(v.startswith("nproc=") for v in _value(args, "--ulimit"))
    assert "--runtime" not in args


def test_gvisor_limits_guest_processes_with_nproc_and_keeps_a_host_backstop() -> None:
    args = DockerSandbox(DockerSandboxConfig(runtime="runsc"))._hardening(**LIMITS)
    assert _value(args, "--runtime") == ["runsc"]
    assert _value(args, "--pids-limit") == [str(16 + RUNSC_HOST_PIDS_HEADROOM)]
    assert "nproc=16:16" in _value(args, "--ulimit")
