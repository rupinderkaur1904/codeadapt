# Development guide

## Prerequisites

* **Docker** (Engine on Linux; Docker Desktop on macOS/Windows). The sandbox needs a
  running daemon. No host bind mounts are used, so Docker Desktop behaves like Linux.
* **uv** ≥ 0.5 (installs Python 3.12+ and the locked dependencies).
* Optional: **gVisor** (`runsc`) registered as a Docker runtime, to test the production
  isolation tier (Linux only).

## Setup from a fresh clone

```bash
git clone https://github.com/rupinderkaur1904/codeadapt && cd codeadapt
cp .env.example .env                                   # optional; defaults work for dev
docker build -t codeadapt-sandbox:gcc14.2-1 sandbox/   # pinned toolchain image
cd backend
uv sync                                                # creates .venv from uv.lock
```

On Windows, run the same commands in PowerShell (or WSL2). Use `copy` instead of `cp`.

## Everyday commands (run in `backend/`)

| Purpose | Command |
| --- | --- |
| All tests | `uv run pytest` |
| Unit tests only (no Docker) | `uv run pytest tests/unit` |
| Sandbox tests only | `uv run pytest -m sandbox` |
| Lint / format / types | `uv run ruff check src tests` · `uv run ruff format src tests` · `uv run mypy` |
| Dependency audit | `uv export --no-hashes --no-emit-project --format requirements-txt > req.txt && uvx pip-audit -r req.txt` |
| Validate problem content (executes it) | `uv run codeadapt-content validate ../content/demo` |
| Synthetic evaluation report (executes it; several minutes) | `uv run codeadapt-eval --json report.json --markdown report.md` |
| Run code by hand | `uv run codeadapt-run main.cpp [harness.cpp] --input in1.txt [--sanitize]` |
| Remove sandbox leftovers after a crash | `docker rm -f $(docker ps -aq --filter label=org.codeadapt.sandbox=1)`; `docker volume rm $(docker volume ls -q --filter label=org.codeadapt.sandbox=1)` |

Sandbox tests are **skipped with a stated reason** if Docker or the image is missing. Set
`CODEADAPT_REQUIRE_SANDBOX=1` to make them fail instead; CI always does.

To test the production tier: `CODEADAPT_SANDBOX_RUNTIME=runsc uv run pytest -m sandbox`.

## Running the API and worker locally

```bash
cd backend
uv run alembic upgrade head                                   # creates ./codeadapt-dev.sqlite3
uv run uvicorn codeadapt.api.app:create_app --factory --port 8000
uv run codeadapt-worker            # second terminal; --once drains the queue and exits
```

Interactive API docs are at `http://localhost:8000/api/docs`. In `dev` and `test`
environments the stub authentication uses the `X-Dev-Role: student|researcher` header
(ADR-013). With `CODEADAPT_ENV=production`, every authenticated endpoint returns 503 until
real authentication arrives in M8. The first submission for a problem takes about 45
seconds locally, because the worker measures and caches that problem's fingerprints for
the current environment. Later submissions take a few seconds.

## Web frontend (`web/`)

```bash
cd web
npm ci
npm run dev            # http://localhost:5173, proxies /api to http://127.0.0.1:8000
```

| Purpose | Command |
| --- | --- |
| Lint / format / types | `npm run lint` · `npm run format:check` · `npm run typecheck` |
| Component tests | `npm test` |
| Browser end-to-end test (starts its own API, worker and preview server; needs Docker + sandbox image) | `npx playwright install chromium` once, then `npm run e2e` |
| Regenerate API types after changing the backend API | `(cd ../backend && uv run codeadapt-openapi) > openapi.json && npm run api:types` |

CI fails if `openapi.json` or `src/api/schema.d.ts` is out of date.

## Docker compose (development only)

`docker compose up --build` builds the sandbox image, runs migrations, and starts the API
(port 8000), the worker and the Vite dev server (port 5173). Data persists in the `appdata`
volume; `docker compose down -v` removes it. The worker mounts the host Docker socket, which
is root-equivalent, so never run this stack where untrusted users can reach it.

## Tested environment

Local results are evidence about *this* environment only.

### M1 (2026-10-15)

| Item | Value |
| --- | --- |
| Host | Linux 6.18.44 x86_64 (cloud VM), Ubuntu 24.04.5 userland, running as root |
| Docker | Engine 29.8.2, runtime runc, cgroup **v1** (cgroupfs driver), builtin seccomp profile |
| Sandbox image | `codeadapt-sandbox:gcc14.2-1` on `gcc:14.2.0@sha256:b99b86a2…f5d24c`; g++ 14.2.0 |
| Python / uv | CPython 3.13.16 / uv 0.11.32 |
| Results | `pytest`: **70 passed, 0 skipped, 0 failed** (42 unit, 28 sandbox; ≈ 49 s). `ruff check`, `ruff format --check`, `mypy --strict`: clean. `pip-audit`: no known vulnerabilities. No labelled containers or volumes left afterwards. |
| Not tested | gVisor (`runsc`) runtime; cgroup v2 hosts; macOS/Windows Docker Desktop; arm64. GitHub Actions (ubuntu-24.04 runner) is the second reference environment: the M1 commit passed all CI steps there, including the sandbox tests. |

### M2 (2026-10-15)

Same environment as M1. `pytest`: **106 passed, 0 skipped, 0 failed** (77 unit, 29 sandbox;
about 92 s). `ruff check`, `ruff format --check` and `mypy --strict` were clean.
`codeadapt-content validate ../content/demo` reported `RESULT ok` with no warnings.

### M3 (2026-10-15)

Same environment as M1. `pytest`: **138 passed, 0 skipped, 0 failed** (107 unit, 31 sandbox; about 3.5 min).
`ruff check`, `ruff format --check` and `mypy --strict` were clean. A manual run with
`alembic upgrade`, `uvicorn` and `codeadapt-worker --once` against SQLite processed a
submission end to end. PostgreSQL is not exercised yet: the SQL is written to be portable
and the queue uses conditional updates, but no test runs against PostgreSQL. This is
tracked for M8.

### M4 (2026-10-15)

Same environment as M1, plus Node 22.22.0 and Chromium (Playwright 1.56.1). `npm test`:
11 passed. Lint, format check, `tsc` and `vite build` were clean, and `npm audit` found 0
vulnerabilities. `npx playwright test`: 1 passed (about 1.2 min, most of it the first
fingerprint measurement). **Not verified locally:** `docker compose build`, because base
images could not be downloaded here (Docker Hub returned 429, GHCR was blocked, and PyPI was
unreachable from build containers). The CI `compose` job covers it.

### M5 (2026-10-15)

Same environment as M1. `pytest`: **152 passed, 0 skipped, 0 failed** (122 unit, 30
sandbox; about 5.7 min). `npm test`: 12 passed. `npx playwright test`: 1 passed (about
1.9 min, because the first fingerprint measurement now includes the sanitiser build).
Lint, format and type checks were clean.

### M6 (2026-10-15)

Same environment as M1. `pytest` with `CODEADAPT_REQUIRE_SANDBOX=1`: **173 passed, 0
skipped, 0 failed** (142 unit, 31 sandbox; about 12.4 min, mostly the first fingerprint
measurement of three problems). `npm test`: 15 passed. `npx playwright test`: 1 passed
(about 2.0 min). `codeadapt-content validate ../content/demo` reported `RESULT ok` for all
three problems with no warnings. Lint, format, type and API-type drift checks were clean.
No sandbox containers or volumes were left behind.

### M7 (2026-10-15)

Same environment as M1. `pytest` with `CODEADAPT_REQUIRE_SANDBOX=1`: **179 passed, 0
skipped, 0 failed** (147 unit, 32 sandbox; about 14.6 min). `npm test`: 18 passed.
`npx playwright test`: 1 passed (about 1.8 min). `codeadapt-eval` over all 17 held-out
cases took about 8.5 min; two separate invocations produced byte-identical JSON and
Markdown reports (saved as docs/evaluation/synthetic-2026-10-15.md). Lint, format, type and
API-type drift checks were clean. No sandbox containers or volumes were left behind.

### CE0 and review resolution (2026-10-15)

Same environment as M1. `pytest` with `CODEADAPT_REQUIRE_SANDBOX=1`: **200 passed, 1
failed** in the full run (169 unit, 32 sandbox; about 14 min). The failure was
`test_lower_bound_heldout_evaluation_is_reproducible`, aborted by
`SandboxUnavailableError: docker kill timed out`: `docker kill` on a timed-out container
exceeded its 15 s limit while the host's load average was about 8 on 4 cores. Re-run alone,
it passed (1 passed, 2.8 min). The same timeout once aborted a `codeadapt-eval` run, and
appeared in the Playwright run, where the worker requeued the job as designed. It is an
infrastructure timeout, not a test result. The harness aborting on it, rather than
recording an infrastructure error for the affected case, is a known limit for M8. No
sandbox containers were left behind. `npm test`: 18 passed. `npx playwright test`:
1 passed (2.3 min). `codeadapt-content report` produced byte-identical reports on two
runs. Held-out and calibration reports for both methods are in
docs/evaluation/review-2026-10-15/. Lint, format, type and API-type drift checks were
clean.

On GitHub Actions (commit d4c218a), the web and compose jobs passed. The backend job
failed once on the same `docker kill` timeout and passed on re-run. The end-to-end job
then failed: `upper_bound_confusion` produced empty output on one run of `large_absent`,
so worker-side validation rejected the content as non-deterministic and the job failed.
Execution-layer reliability under load is an open issue.

Follow-up (ADR-020): kill wait raised to 60 s, client/container exit mismatch classified as
an infrastructure error, and fingerprint measurement re-measures infrastructure errors.
Unit: 174 passed. Sandbox execution, security and demo-content tests: 29 passed. The lost
output was not reproduced in 200 stressed local runs, so whether the mismatch check
catches it is not yet shown.

### C1–C2, C6 comparison and ADR-020 regression tests (2026-10-16)
Same environment. `pytest` with `CODEADAPT_REQUIRE_SANDBOX=1`: **214 passed, 0 skipped,
0 failed** (≈ 15 min). `ruff check`, `ruff format --check`, `mypy --strict`: clean.
`codeadapt-content validate --repeats 3` on lower-bound after C1–C2: valid, 0 errors,
0 warnings, 1 documented limitation (E2). Held-out and calibration comparisons:
docs/evaluation/c6-2026-10-16/. The ADR-020 regression tests use a fake `docker` binary;
they do not reproduce the original CI lost-output failure.
