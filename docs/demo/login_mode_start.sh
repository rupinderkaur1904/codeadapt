#!/usr/bin/env sh
# Login-mode rehearsal without compose: same settings as compose.demo.yaml, on localhost.
set -eu
# Usage: docs/demo/login_mode_start.sh /absolute/scratch/dir  (needs Docker and the sandbox image).
# Starts the worker and the API (port 8010) in the background; stop both by PID when done.
mkdir -p "$1"
cd "$(dirname "$0")/../../backend"
export CODEADAPT_ENV=production
export CODEADAPT_DATABASE_URL="sqlite:///$1/demo.sqlite3"
export CODEADAPT_WORKER_POLL_SECONDS=0.5
export CODEADAPT_ALLOWED_HOSTS=localhost,127.0.0.1   # ADR-040
export CODEADAPT_SANDBOX_ALLOW_RUNC=local-demo-only  # ADR-040: local rehearsal only
rm -f "$1"/demo.sqlite3*
uv run alembic upgrade head
echo 'student demo password' | uv run codeadapt-admin create-user demo-student --role student --data-class dev
echo 'researcher demo password' | uv run codeadapt-admin create-user demo-researcher --role researcher --data-class dev
uv run codeadapt-worker > "$1/worker.log" 2>&1 &
uv run uvicorn codeadapt.api.app:create_app --factory --host 127.0.0.1 --port 8010 > "$1/api.log" 2>&1 &
