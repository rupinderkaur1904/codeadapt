#!/usr/bin/env sh
# Starts a throwaway API + worker for the browser end-to-end test.
# Requires Docker and the sandbox image (see docs/development.md).
set -eu
cd "$(dirname "$0")/../../backend"
export CODEADAPT_ENV=test
export CODEADAPT_DATABASE_URL="sqlite:///$(pwd)/.e2e.sqlite3"
export CODEADAPT_WORKER_POLL_SECONDS=0.2
rm -f .e2e.sqlite3 .e2e.sqlite3-*
uv run alembic upgrade head
uv run codeadapt-worker &
WORKER=$!
trap 'kill "$WORKER" 2>/dev/null || true' EXIT INT TERM
uv run uvicorn codeadapt.api.app:create_app --factory --host 127.0.0.1 --port 8000
