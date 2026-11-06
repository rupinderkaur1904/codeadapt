"""`codeadapt-worker`: the runner process. Only this process talks to Docker."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import socket

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


async def run(settings: Settings, *, once: bool = False) -> int:
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
    worker_id = f"{socket.gethostname()}:{os.getpid()}"
    processed = 0
    while True:
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
            return processed
        else:
            await asyncio.sleep(settings.worker_poll_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codeadapt-worker")
    parser.add_argument("--once", action="store_true", help="drain the queue, then exit")
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    logs.configure(production=settings.env is Environment.PRODUCTION)
    processed = asyncio.run(run(settings, once=args.once))
    log.info("processed %d job(s)", processed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
