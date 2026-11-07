"""`codeadapt-worker`: the runner process. Only this process talks to Docker."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import signal
import socket
import sys
import time
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from codeadapt import logs
from codeadapt.adaptation import PolicyV1
from codeadapt.config import ConfigError, Environment, Settings
from codeadapt.content.catalogue import Catalogue
from codeadapt.db import queue
from codeadapt.db.models import Job
from codeadapt.db.session import make_engine, make_session_factory
from codeadapt.diagnosis import FingerprintConsistencyV1
from codeadapt.execution import SandboxUnavailableError
from codeadapt.execution.docker import DockerSandbox, DockerSandboxConfig
from codeadapt.worker.pipeline import Pipeline

log = logging.getLogger("codeadapt.worker")


async def heartbeat(
    sessions: sessionmaker[Session], job: Job, *, lease_seconds: float, interval: float
) -> None:
    """Renew the job's lease every `interval` seconds until cancelled or the claim is lost."""
    while True:
        await asyncio.sleep(interval)
        with sessions() as session:
            if not queue.renew(session, job, lease_seconds=lease_seconds):
                log.warning("lease renewal for job %s failed: the claim was lost", job.id)
                return


async def handle_with_heartbeat(
    pipeline: Pipeline, sessions: sessionmaker[Session], job: Job, *, lease_seconds: float
) -> None:
    """Run one job while keeping its lease alive (ADR-031)."""
    beat = asyncio.create_task(
        heartbeat(sessions, job, lease_seconds=lease_seconds, interval=lease_seconds / 3)
    )
    try:
        await pipeline.handle(job)
    finally:
        beat.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await beat


async def require_production_runtime(settings: Settings, sandbox: DockerSandbox) -> None:
    """ADR-040: in production, student code runs under gVisor or not at all.

    The worker refuses to start unless ``CODEADAPT_SANDBOX_RUNTIME`` names a ``runsc``
    runtime that the Docker daemon has registered. Every container is then started with
    ``--runtime <that name>``, so if the runtime later disappears Docker fails the run (an
    infrastructure error) instead of falling back to runc. The single exception is the
    explicit ``CODEADAPT_SANDBOX_ALLOW_RUNC=local-demo-only`` of compose.demo.yaml.
    """
    if settings.env is not Environment.PRODUCTION:
        return
    runtime = sandbox.config.runtime
    if not sandbox.is_gvisor or runtime is None:
        if settings.allow_runc_in_production:
            log.warning(
                "PRODUCTION WORKER RUNNING STUDENT CODE WITHOUT gVisor "
                "(CODEADAPT_SANDBOX_ALLOW_RUNC=local-demo-only). Local demo only: never "
                "expose this stack to students."
            )
            return
        raise ConfigError(
            "production requires CODEADAPT_SANDBOX_RUNTIME=runsc (gVisor); the worker will not "
            "run student code under the default runtime"
        )
    if runtime not in await sandbox.registered_runtimes():
        raise SandboxUnavailableError(
            f"container runtime {runtime!r} is not registered with the Docker daemon; "
            "install gVisor (runsc install) and restart Docker"
        )


HEARTBEAT_INTERVAL_SECONDS = 10.0
HEARTBEAT_MAX_AGE_SECONDS = 60.0


async def heartbeat_file(path: Path, interval: float = HEARTBEAT_INTERVAL_SECONDS) -> None:
    """Touch ``path`` every ``interval`` seconds while the event loop is responsive.

    Jobs await Docker without blocking the loop, so a long job keeps the file fresh; a hung
    loop or a dead process lets it go stale (ADR-042).
    """
    while True:
        try:
            await asyncio.to_thread(path.touch)
        except OSError as exc:
            # Keep serving jobs; the stale file makes the health check report the problem.
            log.warning("cannot write the heartbeat file %s: %s", path, exc)
        await asyncio.sleep(interval)


def check_heartbeat(path: Path, max_age: float = HEARTBEAT_MAX_AGE_SECONDS) -> int:
    """Exit status for a container health check: 0 if the heartbeat is fresh."""
    try:
        age = time.time() - path.stat().st_mtime
    except FileNotFoundError:
        print(f"unhealthy: no heartbeat file at {path}", file=sys.stderr)
        return 1
    if age > max_age:
        print(f"unhealthy: last heartbeat {age:.0f} s ago", file=sys.stderr)
        return 1
    print(f"healthy: last heartbeat {age:.0f} s ago")
    return 0


async def serve(
    pipeline: Pipeline,
    sessions: sessionmaker[Session],
    settings: Settings,
    *,
    once: bool = False,
    stop: asyncio.Event | None = None,
) -> int:
    """Claim and process jobs until the queue is empty (``once``) or ``stop`` is set.

    A stop request never interrupts a job: the current job finishes and is recorded, then
    the loop exits without claiming another (ADR-042). If the process is killed anyway, the
    job's lease expires and another worker picks it up (ADR-031).
    """
    stop = stop or asyncio.Event()
    worker_id = f"{socket.gethostname()}:{os.getpid()}"
    processed = 0
    while not stop.is_set():
        with sessions() as session:
            job = queue.claim_next(
                session,
                worker_id,
                lease_seconds=settings.job_lease_seconds,
                max_attempts=settings.job_max_attempts,
            )
        if job is not None:
            log.info("processing job %s (submission %s)", job.id, job.submission_id)
            await handle_with_heartbeat(
                pipeline, sessions, job, lease_seconds=settings.job_lease_seconds
            )
            processed += 1
        elif once:
            break
        else:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=settings.worker_poll_seconds)
    if stop.is_set():
        log.info("stop requested: no further jobs will be claimed")
    return processed


def _install_stop_handlers(stop: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):  # not available on Windows
            loop.add_signal_handler(sig, stop.set)


async def run(settings: Settings, *, once: bool = False, warm_up: bool = False) -> int:
    sessions = make_session_factory(make_engine(settings.database_url))
    sandbox = DockerSandbox(DockerSandboxConfig.from_env())
    await sandbox.check_available()
    await require_production_runtime(settings, sandbox)
    removed = await sandbox.reap()
    if removed:
        log.info("removed %d leftover sandbox objects", removed)
    catalogue = Catalogue.load(settings.content_dir)
    with sessions() as session:
        catalogue.sync(session)
    pipeline = Pipeline(
        sandbox,
        sessions,
        catalogue,
        FingerprintConsistencyV1(),
        PolicyV1(version=settings.policy_version),
    )
    if warm_up:
        results = await pipeline.warm_up()
        invalid = sorted(slug for slug, ok in results.items() if not ok)
        log.info("warm-up measured %d content version(s)", len(results))
        if invalid:
            log.error("content failed validation during warm-up: %s", ", ".join(invalid))
            return -1
        return len(results)
    stop = asyncio.Event()
    _install_stop_handlers(stop)
    beat = (
        asyncio.create_task(heartbeat_file(settings.worker_heartbeat_file))
        if settings.worker_heartbeat_file is not None
        else None
    )
    try:
        return await serve(pipeline, sessions, settings, once=once, stop=stop)
    finally:
        if beat is not None:
            beat.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await beat


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codeadapt-worker")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="drain the queue, then exit")
    mode.add_argument(
        "--warm-up",
        action="store_true",
        help="measure and store fingerprints for every content version, then exit",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="health check: exit 0 if the running worker's heartbeat file is fresh",
    )
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    if args.check:
        if settings.worker_heartbeat_file is None:
            parser.error("--check needs CODEADAPT_WORKER_HEARTBEAT_FILE")
        return check_heartbeat(settings.worker_heartbeat_file)
    logs.configure(production=settings.env is Environment.PRODUCTION)
    result = asyncio.run(run(settings, once=args.once, warm_up=args.warm_up))
    if args.warm_up:
        return 1 if result < 0 else 0
    log.info("processed %d job(s)", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
