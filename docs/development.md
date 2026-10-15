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
| Run code by hand | `uv run codeadapt-run main.cpp [harness.cpp] --input in1.txt [--sanitize]` |
| Remove sandbox leftovers after a crash | `docker rm -f $(docker ps -aq --filter label=org.codeadapt.sandbox=1)`; `docker volume rm $(docker volume ls -q --filter label=org.codeadapt.sandbox=1)` |

Sandbox tests are **skipped with a stated reason** if Docker or the image is missing. Set
`CODEADAPT_REQUIRE_SANDBOX=1` to make them fail instead; CI always does.

To test the production tier: `CODEADAPT_SANDBOX_RUNTIME=runsc uv run pytest -m sandbox`.

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
