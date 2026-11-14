# CodeAdapt

CodeAdapt is a research prototype of an evidence-driven, adaptive C++ practice and
diagnostic platform. Most coding platforms only say whether a submission passed. CodeAdapt
runs a submission against diagnostic tests in a sandbox, records what it observed, works out
which known implementation error the evidence supports (and abstains when it supports none),
recommends a follow-up exercise, and uses the next attempt as new evidence.

```
Submission → Execution evidence → Interpretable diagnosis → Targeted practice → New evidence → Adaptation
```

Observed behaviour is not a student's cognitive state. The system keeps observations,
inferences and learning outcomes separate, and every piece of feedback can be traced back to
the evidence behind it.

> **Research status in one line.** CodeAdapt has not been validated with real students. The
> learner model uses assumed parameters, and every evaluation result so far is synthetic or
> author-written, so none of it is real-student accuracy or a learning gain. See
> [Evaluation status and limitations](#evaluation-status-and-limitations).

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Repository layout](#repository-layout)
- [Local setup](#local-setup)
- [Tests and CI](#tests-and-ci)
- [Deployment](#deployment)
- [Evaluation status and limitations](#evaluation-status-and-limitations)
- [Project status](#project-status)
- [Documentation](#documentation)
- [Licence](#licence)

## Features

| Feature | What it does | Where |
| --- | --- | --- |
| **Sandboxed execution** | Compiles and runs each submission in a fresh Docker container per compile and per test, with no network, resource limits and a pinned GCC 14.2 toolchain. Development uses runc; a production worker refuses to start unless gVisor (`runsc`) is registered (ADR-040). Repeat runs and an optional sanitiser build separate genuine failures from infrastructure noise. | `backend/src/codeadapt/execution`, `sandbox/`, [docs/security.md](docs/security.md) |
| **Fingerprint diagnosis** | A deterministic, interpretable method (`fingerprint_consistency`, production version 1.3). Each problem has hand-written error models whose test-by-test behaviour is measured in the sandbox; a submission is matched against those fingerprints. Collisions, ambiguity, non-termination and unmodelled behaviour lead to abstention or qualified feedback, never to a forced guess. Earlier method versions 1.1 and 1.2 stay selectable for comparison. | `backend/src/codeadapt/diagnosis`, [docs/methodology.md](docs/methodology.md) |
| **Evidence layer** | Turns runs into skill observations through a ledger with explicit rules: unreliable, inconclusive or infrastructure-failed runs never become negative evidence, and qualified diagnoses add no failures. | `backend/src/codeadapt/evidence`, `backend/src/codeadapt/adaptation/ledger.py` |
| **BKT learner model** | Bayesian knowledge tracing per skill, using the first eligible, reliably evaluated attempt per problem version. Parameters are the labelled assumption set `bkt-params-assumed-1`; estimates are shown to researchers only and labelled "estimated under assumed parameters". | `backend/src/codeadapt/learner/bkt.py`, ADR-025 |
| **Recommendations** | A transparent rule-based policy (version 1.5, ADR-038) that ranks follow-up problems from the diagnosis and the evidence. It is a conservative baseline, not an optimised or outcome-evaluated policy. | `backend/src/codeadapt/adaptation/policy_v1.py` |
| **Problem bank** | 25 demo problems in five families (binary search 12, arrays 5, two pointers 3, sliding window 3, prefix sums 2), with 384 diagnostic tests and 122 error models. 20 problems are recommendable; 5 binary-search problems are held back from recommendation. Content is validated by executing it. | `content/demo/`, [docs/content-format.md](docs/content-format.md), [docs/content-design/](docs/content-design/README.md) |
| **Student workspace** | Browser editor (CodeMirror) with problem list, practice page, per-test feedback, diagnosis, recommendation and attempt history. | `web/src/pages` (`/problems`, `/practice/:slug`, `/attempts`) |
| **Researcher console** | Submission traces from evidence to diagnosis and recommendation, learner list and per-learner BKT estimates. | `/research`, `/research/learners`, `/research/submissions/:id` |
| **Accounts and sign-up** | Argon2id passwords, server-side sessions with rotation, CSRF protection, rate limits and an append-only audit log. Optional self-service sign-up, off unless `CODEADAPT_SIGNUP` is set: `open` needs only a username and password, with per-client limits and a daily cap (ADR-046); `invite-code` also needs a code from `codeadapt-admin invite-create` (ADR-044). Sign-up accounts are always students with data class `dev`. Researcher accounts are created only by an operator. | `backend/src/codeadapt/auth`, `backend/src/codeadapt/api/security.py` |
| **Evaluation harness** | `codeadapt-eval` runs held-out and calibration case sets (kept apart) under any method version and writes reproducible JSON/Markdown reports. | `backend/src/codeadapt/evaluation`, `eval/` |

## Architecture

```
 Browser (React SPA)
        │  HTTPS, session cookie + CSRF
        ▼
 Caddy proxy ── serves the web build, forwards /api
        │
        ▼
 FastAPI API ── auth, problems, submissions, feedback, research endpoints
        │  jobs table (queue with conditional updates)
        ▼
 PostgreSQL 16 (SQLite in development)
        ▲
        │  claims jobs, writes runs / diagnosis / evidence / learner model / recommendation
 Worker ── runs each compile and test in a fresh sandbox container (gVisor in production)
```

A submission is stored and queued by the API. The worker claims the job, measures the
problem's error-model fingerprints on first use (cached per environment), runs the
submission, classifies each run, diagnoses it, writes skill evidence, updates the learner
model and stores a recommendation. The API then serves the feedback. In the deployment
topology the API and database run on one host and the worker on a separate runner host
without a public address (ADR-043).

Full description: [docs/architecture.md](docs/architecture.md) and
[docs/component-interfaces.md](docs/component-interfaces.md).

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, Argon2 (argon2-cffi), uvicorn; managed with [uv](https://docs.astral.sh/uv/) |
| Database | PostgreSQL 16 (deployment and CI), SQLite (development) |
| Sandbox | Docker, `gcc:14.2.0` pinned by digest (`codeadapt-sandbox:gcc14.2-1`), gVisor `runsc` in production |
| Frontend | React 19, TypeScript 5.9, Vite, TanStack Query, React Router, CodeMirror |
| Testing | pytest, mypy (strict), ruff, Vitest, Testing Library, Playwright, ESLint, Prettier |
| Deployment | Docker Compose, Caddy, images built in GitHub Actions and published to GHCR, Azure VMs |

## Repository layout

| Path | Contents |
| --- | --- |
| `backend/` | API, worker, diagnosis, evidence, learner model, adaptation, auth, evaluation; tests in `backend/tests/unit` and `backend/tests/sandbox` |
| `web/` | React frontend; component tests in `web/src`, browser end-to-end tests in `web/e2e` |
| `sandbox/` | Dockerfile for the pinned C++ toolchain image |
| `content/demo/` | Public demo problem bank (real study content would live in a private repository, ADR-009) |
| `eval/` | Held-out, calibration, mutation and infrastructure case sets |
| `deploy/` | Production compose files, Dockerfiles, Caddy config, host and backup scripts |
| `docs/` | Architecture, security, methodology, decisions, evaluation reports, deployment guides |
| `compose.yaml`, `compose.demo.yaml` | Local development stack and its login-mode demo overlay |

## Local setup

Local stacks are for development only. The development worker mounts the host Docker
socket, which is root-equivalent, so never expose them beyond `localhost`.

### Option A: Docker Compose (Docker only)

```bash
git clone https://github.com/rupinderkaur1904/codeadapt && cd codeadapt
docker compose up --build          # then open http://localhost:5173
```

This builds the sandbox image, runs migrations and starts the API (port 8000), the worker
and the Vite dev server (port 5173). In development a role switch replaces login. To show
the real login page, add the demo overlay; it creates `demo-student` and `demo-researcher`
(their public, local-only passwords are in `compose.demo.yaml`):

```bash
docker compose -f compose.yaml -f compose.demo.yaml up --build
```

`docker compose down -v` removes the stack and its data.

### Option B: without Compose (Docker, uv, Node 22)

```bash
docker build -t codeadapt-sandbox:gcc14.2-1 sandbox/

cd backend
uv sync
export CODEADAPT_ENV=dev           # an unset CODEADAPT_ENV means production (ADR-040)
uv run alembic upgrade head        # creates ./codeadapt-dev.sqlite3
uv run uvicorn codeadapt.api.app:create_app --factory --port 8000
uv run codeadapt-worker            # in a second terminal (with CODEADAPT_ENV=dev)

cd ../web
npm ci
npm run dev                        # http://localhost:5173, proxies /api to port 8000
```

Interactive API docs are at `http://localhost:8000/api/docs`. The first submission for a
problem takes one to two minutes while the worker measures that problem's fingerprints;
later ones take a few seconds.

Configuration is read only from `CODEADAPT_*` environment variables; nothing loads a `.env`
file automatically. [.env.example](.env.example) lists every variable with its default.

### Useful commands (in `backend/`)

| Purpose | Command |
| --- | --- |
| Run C++ by hand in the sandbox | `uv run codeadapt-run main.cpp --input input.txt` |
| Validate the problem bank (executes it) | `uv run codeadapt-content validate ../content/demo` |
| Held-out evaluation report (several minutes) | `uv run codeadapt-eval --content ../content/demo --heldout ../eval/heldout --json report.json --markdown report.md` |
| Compare method versions | `uv run codeadapt-eval --compare v1.1 v1.2 v1 --markdown comparison.md` |
| Accounts and invite codes | `uv run codeadapt-admin --help` (`create-user`, `set-password`, `invite-create`, `invite-list`, `invite-revoke`, …) |

More detail, including Windows and macOS notes, is in
[docs/development.md](docs/development.md).

## Tests and CI

| Suite | Command | Needs |
| --- | --- | --- |
| Backend unit tests | `cd backend && uv run pytest tests/unit` | nothing |
| Backend sandbox tests | `cd backend && uv run pytest -m sandbox` | Docker and the sandbox image |
| All backend tests | `cd backend && uv run pytest` | Docker (sandbox tests skip with a reason otherwise; `CODEADAPT_REQUIRE_SANDBOX=1` makes them fail) |
| Lint, format, types | `uv run ruff check src tests` · `uv run ruff format --check src tests` · `uv run mypy` | — |
| Frontend | `cd web && npm run lint && npm run format:check && npm run typecheck && npm test` | Node 22 |
| Browser end-to-end | `cd web && npx playwright install chromium && npm run e2e` | Docker and the sandbox image |

GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs on every push and
pull request:

- **backend** and **backend-postgres**: lint, format, mypy, non-sandbox tests on SQLite and
  on PostgreSQL 16, and a dependency audit;
- **sandbox**, **sandbox-postgres** and **sandbox-gvisor**: the sandbox tests in parallel
  shards under runc and under gVisor, plus the full pipeline on PostgreSQL;
- **web**: API-type drift check, lint, format, typecheck, Vitest, build and `npm audit`;
- **e2e**: Playwright against a real API, worker and sandbox;
- **compose**: the development stack builds from a fresh clone and processes a submission;
- **production-images**: production images build and run as non-root, and the app stack
  serves HTTPS with security headers and least-privilege database roles.

[release-images.yml](.github/workflows/release-images.yml) builds the production images and,
on `main`, publishes them to GHCR with an immutable `sha-<commit>` tag.

## Deployment

The production setup is an App VM (Caddy, API, PostgreSQL) and a separate runner VM
(worker with gVisor, no public address) on Azure, pulling CI-built images by digest.
Start with:

- [docs/deployment/azure-deployment-guide.md](docs/deployment/azure-deployment-guide.md): the plan and steps;
- [docs/deployment/production-runbook.md](docs/deployment/production-runbook.md): operating the hosts;
- [docs/deployment/m4-deployment-progress.md](docs/deployment/m4-deployment-progress.md): what has actually been done, with evidence;
- [docs/deployment.md](docs/deployment.md): configuration variables and the gate checklist;
- [docs/deployment/backup-and-restore.md](docs/deployment/backup-and-restore.md) and [docs/deployment/gvisor-verification.md](docs/deployment/gvisor-verification.md).

Secrets live only in `deploy/app.env` and `deploy/runner.env` on the hosts (templates:
`*.env.example`) and are never committed. No real student may be enrolled before the ethics
and security gate (Gate C) is passed.

## Evaluation status and limitations

What has been measured, and what it does **not** show:

- **No real-student validation.** Every evaluated program was written by the error models'
  author (held-out and calibration sets) or generated mechanically (mutation audits). No
  real-student or public-corpus data has been evaluated.
- **Synthetic results are not accuracy.** Held-out cases were written to contain one
  modelled error each, so naming it is close to circular. Under method 1.3 the original author-written
  held-out set (four problems) gets 14 of 26 incorrect programs named, all correctly, with no false alarms on
  correct programs; the mutation audits name only about 9% of incorrect mutants (30 of 323 in
  VAL1-A2). Neither number is a real-world precision or coverage estimate.
- **BKT uses assumed parameters.** `bkt-params-assumed-1` was not fitted. Estimates swing
  widely across plausible parameter values with few observations, so they are researcher-only
  and never shown to students as mastery.
- **Skill mappings are modelling choices.** The problem-to-skill and test-to-skill mappings
  are author-defined and unvalidated; some distinct causes produce identical behaviour and are
  marked `known_limitation` so they add no negative evidence.
- **No learning effect measured.** Nothing shows that CodeAdapt improves learning.
- **Technique is not verified.** A linear scan can pass a problem that asks for binary search;
  only a static check for banned library calls exists.

Details: [docs/evaluation/summary.md](docs/evaluation/summary.md) (all labelled results) and
[docs/limitations.md](docs/limitations.md) (the full list with evidence and open decisions).

## Project status

CodeAdapt is a working research prototype, not a validated or production-ready teaching
tool.

| Area | Status |
| --- | --- |
| Core platform (M0–M7: sandbox, content model, API and worker, student workspace, evidence reliability, adaptation, researcher console, evaluation harness) | done |
| Evidence ledger (EV1), researcher-only BKT (LM1), problem bank of 25 | done |
| Security hardening (fail-closed production config, gVisor required, session and audit hardening, operational safety) | done (ADR-040 to ADR-042) |
| Self-service sign-up (open or invite-code) | done (ADR-044, ADR-046) |
| Azure deployment | in progress: hosts set up and app served over HTTPS; the end-to-end check on the hosts, gVisor host verification steps 5–7, database TLS on the hosts, backups and monitoring are still open |
| Real-data validation (public corpus or student study) | not started: blocked on data-use permission and on ethics review |
| Pilot with real students (Gate C) | not started |

The milestone plan is in [docs/roadmap.md](docs/roadmap.md), decisions in
[docs/decisions.md](docs/decisions.md), and the progress log in
[PROJECT_AUTOPILOT.md](PROJECT_AUTOPILOT.md).

## Documentation

| Document | Contents |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | objective, stack, components, workflow, data model, API, risks |
| [docs/security.md](docs/security.md) | threat model, sandbox design, accounts and audit, verified guarantees, limits |
| [docs/methodology.md](docs/methodology.md) | diagnostic method, adaptation policy, evaluation plan |
| [docs/decisions.md](docs/decisions.md) | architecture decision records (ADR-001 onwards) |
| [docs/content-format.md](docs/content-format.md) | how problems, tests and error models are authored and validated |
| [docs/content-design/](docs/content-design/README.md) | design record for every problem |
| [docs/evaluation/summary.md](docs/evaluation/summary.md) | one-page labelled results (synthetic and author-written only) |
| [docs/limitations.md](docs/limitations.md) | limitations and future work |
| [docs/development.md](docs/development.md) | setup, commands, tested environments |
| [docs/demo.md](docs/demo.md) | demo workflow with observed output |
| [docs/pilot/](docs/pilot/pilot-protocol.md) | draft pilot protocol, consent and data governance (not yet approved or used) |
| [docs/research-report-draft.md](docs/research-report-draft.md) | research report draft (evidence-supported claims only) |
| [docs/presentation/script.md](docs/presentation/script.md) | presentation script; the slides are served by the app at `/presentation` |

## Licence

No open-source licence has been chosen. The repository is publicly visible, but
`backend/pyproject.toml` declares the package as proprietary and there is no `LICENSE`
file, so all rights are reserved by the author: you may read the code, but you need the
author's permission to copy, modify or redistribute it. The demo content in `content/demo/`
is public example material, not study data.
