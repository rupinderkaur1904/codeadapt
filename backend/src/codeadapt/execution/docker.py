"""Docker-based sandbox backend (see docs/security.md §3 for the design).

Every compile and every test run is a separate, hardened container. Source code enters
through a tar stream on stdin into a per-job named volume; nothing on the host filesystem
is bind-mounted and no host environment variable is forwarded.
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import shutil
import tarfile
import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from codeadapt.execution.backend import SandboxUnavailableError
from codeadapt.execution.classify import RawOutcome, classify_compile, classify_run, signal_of
from codeadapt.execution.models import (
    BuildProfile,
    CompileLimits,
    CompileResult,
    CompileStatus,
    EnvironmentInfo,
    RunLimits,
    RunResult,
    SourceFile,
)
from codeadapt.execution.process import ProcessOutcome, run_bounded

LABEL = "org.codeadapt.sandbox"
SANDBOX_USER = "65534:65534"
DEFAULT_IMAGE = "codeadapt-sandbox:gcc14.2-1"
MAX_SOURCE_FILES = 8
MAX_SOURCE_BYTES = 256 * 1024  # all files of one compile, including private harness code
_DOCKER_CLI_TIMEOUT = 60.0
_MIB = 1024 * 1024

# Flags are part of the evidence provenance; change them only with a new profile name.
PROFILE_FLAGS: dict[BuildProfile, tuple[str, ...]] = {
    BuildProfile.STANDARD: ("-std=c++20", "-O2", "-pipe", "-Wall", "-Wextra"),
    BuildProfile.SANITIZE: (
        "-std=c++20",
        "-O1",
        "-g",
        "-pipe",
        "-fno-omit-frame-pointer",
        "-fsanitize=address,undefined",
        "-fno-sanitize-recover=undefined",
    ),
}

_COMPILE_SCRIPT = 'tar -x -f - -C /work/src && cd /work/src && exec "$@"'


@dataclass(frozen=True)
class DockerSandboxConfig:
    image: str = DEFAULT_IMAGE
    # None = the daemon's default runtime (runc). Production requires "runsc" (gVisor).
    runtime: str | None = None
    docker_binary: str = "docker"
    max_concurrency: int = 4
    compile_limits: CompileLimits = field(default_factory=CompileLimits)
    run_limits: RunLimits = field(default_factory=RunLimits)

    @classmethod
    def from_env(cls) -> DockerSandboxConfig:
        return cls(
            image=os.environ.get("CODEADAPT_SANDBOX_IMAGE", DEFAULT_IMAGE),
            runtime=os.environ.get("CODEADAPT_SANDBOX_RUNTIME") or None,
            docker_binary=os.environ.get("CODEADAPT_DOCKER_BINARY", "docker"),
            max_concurrency=int(os.environ.get("CODEADAPT_SANDBOX_MAX_CONCURRENCY", "4")),
        )


@dataclass(frozen=True, slots=True)
class _CliResult:
    returncode: int
    stdout: str
    stderr: str


def _build_tar(sources: Sequence[SourceFile]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for src in sources:
            data = src.content.encode("utf-8")
            info = tarfile.TarInfo(name=src.name)
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _validate_sources(sources: Sequence[SourceFile]) -> list[str]:
    if not sources:
        raise ValueError("at least one source file is required")
    if len(sources) > MAX_SOURCE_FILES:
        raise ValueError(f"at most {MAX_SOURCE_FILES} source files are allowed")
    names = [s.name for s in sources]
    if len(set(names)) != len(names):
        raise ValueError("duplicate source file names")
    total = sum(len(s.content.encode("utf-8")) for s in sources)
    if total > MAX_SOURCE_BYTES:
        raise ValueError(f"sources exceed {MAX_SOURCE_BYTES} bytes")
    units = [n for n in names if n.endswith((".cpp", ".cc"))]
    if not units:
        raise ValueError("no translation unit (.cpp/.cc) to compile")
    return units


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


class DockerSandbox:
    """`SandboxBackend` implementation driving the docker CLI."""

    def __init__(self, config: DockerSandboxConfig | None = None) -> None:
        self.config = config or DockerSandboxConfig()
        self._slots = asyncio.Semaphore(self.config.max_concurrency)
        self._environment: EnvironmentInfo | None = None

    # ------------------------------------------------------------------ docker CLI
    async def _cli(self, *args: str, limit_seconds: float = _DOCKER_CLI_TIMEOUT) -> _CliResult:
        binary = shutil.which(self.config.docker_binary)
        if binary is None:
            raise SandboxUnavailableError(f"docker binary {self.config.docker_binary!r} not found")
        proc = await asyncio.create_subprocess_exec(
            binary,
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), limit_seconds)
        except TimeoutError as exc:
            proc.kill()
            await proc.wait()
            raise SandboxUnavailableError(f"docker {args[0]} timed out") from exc
        return _CliResult(proc.returncode or 0, _decode(out), _decode(err))

    def _binary(self) -> str:
        binary = shutil.which(self.config.docker_binary)
        if binary is None:
            raise SandboxUnavailableError(f"docker binary {self.config.docker_binary!r} not found")
        return binary

    # ------------------------------------------------------------------ public API
    async def check_available(self) -> None:
        """Raise `SandboxUnavailableError` unless the daemon and image are usable."""
        info = await self._cli("version", "--format", "{{.Server.Version}}")
        if info.returncode != 0:
            raise SandboxUnavailableError(f"docker daemon unavailable: {info.stderr.strip()}")
        image = await self._cli("image", "inspect", "--format", "{{.Id}}", self.config.image)
        if image.returncode != 0:
            raise SandboxUnavailableError(
                f"sandbox image {self.config.image!r} missing; build it with "
                f"`docker build -t {self.config.image} sandbox/`"
            )

    async def environment(self) -> EnvironmentInfo:
        if self._environment is not None:
            return self._environment
        await self.check_available()
        image_id = (
            await self._cli("image", "inspect", "--format", "{{.Id}}", self.config.image)
        ).stdout.strip()
        engine = (await self._cli("version", "--format", "{{.Server.Version}}")).stdout.strip()
        info = await self._cli("info", "--format", "{{.DefaultRuntime}}|{{.KernelVersion}}")
        default_runtime, _, kernel = info.stdout.strip().partition("|")
        compiler = await self._cli(
            "run",
            "--rm",
            *self._hardening(memory_mib=256, pids=16, open_files=64, cpu_seconds=10, fsize=0),
            self.config.image,
            "g++",
            "--version",
        )
        if compiler.returncode != 0:
            raise SandboxUnavailableError(f"cannot query compiler: {compiler.stderr.strip()}")
        self._environment = EnvironmentInfo(
            backend="docker",
            image=self.config.image,
            image_id=image_id,
            compiler_version=compiler.stdout.splitlines()[0].strip(),
            container_runtime=self.config.runtime or default_runtime,
            engine_version=engine,
            host_kernel=kernel,
        )
        return self._environment

    @asynccontextmanager
    async def job(self) -> AsyncIterator[DockerSandboxJob]:
        """A fresh workspace volume, removed (with any containers) on exit."""
        await self.check_available()
        job_id = uuid.uuid4().hex[:16]
        volume = f"codeadapt-job-{job_id}"
        created = await self._cli("volume", "create", "--label", f"{LABEL}=1", volume)
        if created.returncode != 0:
            raise SandboxUnavailableError(f"cannot create job volume: {created.stderr.strip()}")
        job = DockerSandboxJob(self, job_id, volume)
        try:
            yield job
        finally:
            await job.close()

    async def reap(self) -> int:
        """Remove every labelled sandbox container and volume left by a crashed worker.

        Call only when no job is active on this Docker daemon (e.g. at worker start-up).
        """
        removed = 0
        ps = await self._cli("ps", "-aq", "--filter", f"label={LABEL}=1")
        for cid in ps.stdout.split():
            if (await self._cli("rm", "-f", cid)).returncode == 0:
                removed += 1
        vols = await self._cli("volume", "ls", "-q", "--filter", f"label={LABEL}=1")
        for vol in vols.stdout.split():
            if (await self._cli("volume", "rm", "-f", vol)).returncode == 0:
                removed += 1
        return removed

    # ------------------------------------------------------------------ internals
    def _hardening(
        self, *, memory_mib: int, pids: int, open_files: int, cpu_seconds: int, fsize: int
    ) -> list[str]:
        args = [
            # A minimal init (tini) is PID 1, so the submission is an ordinary process:
            # PID 1 ignores default-action signals, which would otherwise disable
            # SIGXCPU from the CPU rlimit and change abort()/raise() semantics.
            "--init",
            "--label",
            f"{LABEL}=1",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--ipc",
            "none",
            "--user",
            SANDBOX_USER,
            "--hostname",
            "sandbox",
            "--log-driver",
            "none",
            "--cpus",
            "1",
            "--pids-limit",
            str(pids),
            "--memory",
            f"{memory_mib}m",
            "--memory-swap",
            f"{memory_mib}m",
            "--ulimit",
            f"cpu={cpu_seconds}:{cpu_seconds + 1}",
            "--ulimit",
            f"nofile={open_files}:{open_files}",
            "--ulimit",
            "core=0:0",
            "--ulimit",
            f"fsize={fsize}:{fsize}",
        ]
        if self.config.runtime:
            args += ["--runtime", self.config.runtime]
        return args

    async def _run_container(
        self,
        *,
        name: str,
        docker_args: list[str],
        stdin: bytes,
        deadline: float,
        stdout_cap: int,
        stderr_cap: int,
        kill_on_overflow: bool,
    ) -> tuple[ProcessOutcome, RawOutcome]:
        argv = [self._binary(), "run", "-i", "--name", name, *docker_args]

        async def kill() -> None:
            # The workload is already bounded by its CPU rlimit, memory and pids limits;
            # this limit only bounds how long we wait for a busy daemon to confirm.
            await self._cli("kill", name, limit_seconds=_DOCKER_CLI_TIMEOUT)

        async with self._slots:
            try:
                proc = await run_bounded(
                    argv,
                    stdin=stdin,
                    deadline_seconds=deadline,
                    stdout_cap=stdout_cap,
                    stderr_cap=stderr_cap,
                    kill=kill,
                    kill_on_overflow=kill_on_overflow,
                )
                state = await self._cli("inspect", "--format", "{{json .State}}", name)
            finally:
                await self._cli("rm", "-f", name, limit_seconds=30)

        started = False
        exit_code: int | None = None
        oom = False
        if state.returncode == 0:
            st = json.loads(state.stdout)
            started = not str(st.get("StartedAt", "")).startswith("0001-")
            exit_code = int(st["ExitCode"]) if started else None
            oom = bool(st.get("OOMKilled", False))
        overflow = kill_on_overflow and (proc.stdout_overflow or proc.stderr_overflow)
        raw = RawOutcome(
            started=started,
            exit_code=exit_code,
            oom_killed=oom,
            timed_out=proc.timed_out,
            output_overflow=overflow,
            stream_mismatch=(
                started
                and not proc.timed_out
                and not overflow
                and exit_code is not None
                and proc.returncode != exit_code
            ),
        )
        return proc, raw


def _infra_detail(raw: RawOutcome, kind: str) -> str:
    if not raw.started:
        return f"{kind} container did not start"
    if raw.stream_mismatch:
        return f"{kind} output stream disagreed with the container's exit status"
    return ""


class DockerSandboxJob:
    def __init__(self, sandbox: DockerSandbox, job_id: str, volume: str) -> None:
        self._sandbox = sandbox
        self.job_id = job_id
        self.volume = volume
        self._seq = 0
        self._compiled: set[BuildProfile] = set()

    def _name(self, kind: str) -> str:
        self._seq += 1
        return f"codeadapt-{self.job_id}-{kind}-{self._seq}"

    async def compile(
        self, sources: list[SourceFile], profile: BuildProfile = BuildProfile.STANDARD
    ) -> CompileResult:
        units = _validate_sources(sources)
        limits = self._sandbox.config.compile_limits
        flags = PROFILE_FLAGS[profile]
        docker_args = [
            *self._sandbox._hardening(
                memory_mib=limits.memory_mib,
                pids=limits.pids,
                open_files=limits.open_files,
                cpu_seconds=limits.cpu_seconds,
                fsize=limits.max_file_mib * _MIB,
            ),
            "--tmpfs",  # /tmp inside the container, not on the host
            f"/tmp:rw,nosuid,nodev,noexec,size={limits.tmpfs_mib}m,mode=1777",  # noqa: S108
            "--mount",
            f"type=volume,src={self.volume},dst=/work",
            self._sandbox.config.image,
            "sh",
            "-c",
            _COMPILE_SCRIPT,
            "sh",
            "g++",
            *flags,
            "-o",
            f"/work/bin/{profile.value}",
            *units,
        ]
        proc, raw = await self._sandbox._run_container(
            name=self._name("compile"),
            docker_args=docker_args,
            stdin=_build_tar(sources),
            deadline=limits.wall_seconds,
            stdout_cap=limits.stdout_bytes,
            stderr_cap=limits.stderr_bytes,
            # Long template errors are legitimate; truncate rather than kill.
            kill_on_overflow=False,
        )
        status = classify_compile(raw)
        if status is CompileStatus.OK:
            self._compiled.add(profile)
        return CompileResult(
            status=status,
            profile=profile,
            flags=flags,
            exit_code=raw.exit_code,
            diagnostics=_decode(proc.stderr),
            diagnostics_truncated=proc.stderr_overflow,
            wall_ms=proc.wall_ms,
            detail=_infra_detail(raw, "compile"),
        )

    async def run(
        self,
        stdin: bytes,
        profile: BuildProfile = BuildProfile.STANDARD,
        limits: RunLimits | None = None,
    ) -> RunResult:
        if profile not in self._compiled:
            raise RuntimeError(f"profile {profile.value!r} has not been compiled successfully")
        limits = limits or self._sandbox.config.run_limits
        if len(stdin) > limits.stdin_bytes:
            raise ValueError(f"stdin exceeds {limits.stdin_bytes} bytes")
        docker_args = [
            *self._sandbox._hardening(
                memory_mib=limits.memory_mib,
                pids=limits.pids,
                open_files=limits.open_files,
                cpu_seconds=limits.cpu_seconds,
                fsize=0,
            ),
            "--mount",
            f"type=volume,src={self.volume},dst=/work,readonly",
            "--workdir",
            "/",
            self._sandbox.config.image,
            f"/work/bin/{profile.value}",
        ]
        proc, raw = await self._sandbox._run_container(
            name=self._name("run"),
            docker_args=docker_args,
            stdin=stdin,
            deadline=limits.wall_seconds,
            stdout_cap=limits.stdout_bytes,
            stderr_cap=limits.stderr_bytes,
            kill_on_overflow=True,
        )
        return RunResult(
            status=classify_run(raw),
            exit_code=raw.exit_code,
            signal=signal_of(raw.exit_code),
            stdout=_decode(proc.stdout),
            stdout_truncated=proc.stdout_overflow,
            stderr=_decode(proc.stderr),
            stderr_truncated=proc.stderr_overflow,
            wall_ms=proc.wall_ms,
            oom_killed=raw.oom_killed,
            timed_out=raw.timed_out,
            detail=_infra_detail(raw, "run"),
        )

    async def close(self) -> None:
        await self._sandbox._cli("volume", "rm", "-f", self.volume, limit_seconds=30)
