# Production images for the API and the worker (ADR-042, Milestone 3).
# Build from the repository root:
#   docker build -f deploy/backend.Dockerfile --target api    -t codeadapt-api:<tag> .
#   docker build -f deploy/backend.Dockerfile --target worker -t codeadapt-worker:<tag> .
# The development image is backend/Dockerfile.

FROM python:3.13-slim@sha256:09a17cad02668ae61ece136b4fd36ac3849e14f670ebedb637ea3e15580525bc AS base
RUN pip install --no-cache-dir uv==0.11.32 \
    && groupadd --system --gid 10001 codeadapt \
    && useradd --system --uid 10001 --gid codeadapt --home-dir /app --shell /usr/sbin/nologin codeadapt
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    CODEADAPT_ENV=production CODEADAPT_CONTENT_DIR=/app/content/demo
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY backend/alembic.ini ./
COPY backend/migrations ./migrations
COPY backend/src ./src
# Editable install: migrate.py finds alembic.ini and migrations/ relative to src/.
RUN uv sync --locked --no-dev
# Demo content ships in the image; a deployment with private study content mounts it
# read-only over /app/content (ADR-009).
COPY content /app/content

# ---------------------------------------------------------------- API: no Docker, non-root
FROM base AS api
USER codeadapt:codeadapt
EXPOSE 8000
# Liveness, sent with the first allowed Host (the API refuses unknown Host headers).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request as u; h = os.environ['CODEADAPT_ALLOWED_HOSTS'].split(',')[0].strip(); u.urlopen(u.Request('http://127.0.0.1:8000/api/v1/health', headers={'Host': h}), timeout=4)"]
# --proxy-headers with --forwarded-allow-ips naming ONLY the reverse proxy (never '*'),
# so the login throttle sees real clients (deployment.md §7). --no-access-log: the app
# logs requests itself without query strings or client addresses (ADR-042).
# --log-config: uvicorn's own loggers go through the app's redacting handler (R8).
ENV FORWARDED_ALLOW_IPS=127.0.0.1
CMD ["sh", "-c", "exec uvicorn codeadapt.api.app:create_app --factory --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips \"$FORWARDED_ALLOW_IPS\" --no-access-log --log-config /app/backend/src/codeadapt/uvicorn_logging.json"]

# ---------------------------------------------------------------- worker: Docker CLI
FROM base AS worker
# The Docker CLI only; the daemon (with gVisor) runs on the runner host. The socket is
# root-equivalent on that host (docs/deployment/milestone-3-architecture.md §4). The
# process runs as uid 10001 and reaches the socket through the host's docker group,
# granted at run time (compose: group_add with the socket's gid).
COPY --from=docker:29-cli@sha256:2357639ad1ea7d0194134bf3292622fd4e562483966ed674e5d7c945b5f3b28d /usr/local/bin/docker /usr/local/bin/docker
# DOCKER_CONFIG: the root filesystem is read-only at run time; the CLI keeps state in /tmp.
ENV CODEADAPT_SANDBOX_RUNTIME=runsc CODEADAPT_WORKER_HEARTBEAT_FILE=/tmp/codeadapt-worker.heartbeat \
    DOCKER_CONFIG=/tmp/.docker
USER codeadapt:codeadapt
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["codeadapt-worker", "--check"]
STOPSIGNAL SIGTERM
CMD ["codeadapt-worker"]
