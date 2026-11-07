# Milestone 3 baseline audit (M3.1)

Date: 2026-11-07. Scope: how ready CodeAdapt is to run a small, controlled, ethically
approved student pilot, and what blocks it. This audit changes no code.

**Bottom line.** The application code on `main` is in good shape for a pilot: CI is green,
authentication and authorization were hardened in Milestone 2, and the sandbox is tested
under gVisor in CI. What is missing is everything around the code. Nothing is deployed,
there is no production image, readiness probe, monitoring or tested PostgreSQL restore, a
few log paths can leak data, and the pilot governance documents do not exist yet. None of
the blockers needs a change to the research method.

## 1. Baseline reference

| Item | Value | How checked |
| --- | --- | --- |
| Repository | `rupinderkaur1904/codeadapt`, default branch `main` | GitHub API |
| `main` head | `eff4dc7` (merge of PR #3, ADR-041) | `git fetch origin main` |
| CI on `main` head | 18 of 18 check runs succeeded | GitHub check runs for `eff4dc7` |
| Branch protection | `main` protected, strict required status checks | GitHub API |
| Working branch | `claude/project-thread-qk4fuc`, restarted from `eff4dc7` (its previous PR was merged; fast-forward, no force push) | `git merge-base --is-ancestor` |

### Test baseline reproduced in the cloud container

| Check | Command (as CI runs it) | Result |
| --- | --- | --- |
| Backend, SQLite | `uv run pytest` | 714 passed, 39 skipped (sandbox tests: no Docker daemon) |
| Backend, PostgreSQL 16 | same, with `CODEADAPT_TEST_POSTGRES_URL` | 714 passed, 39 skipped |
| Lint and format | `ruff check src tests`, `ruff format --check src tests` | clean |
| Types | `mypy` | no issues in 116 files |
| Python dependencies | `uvx pip-audit` on the exported lock | no known vulnerabilities |
| Web | `vitest run`, `typecheck`, `lint` | 45 passed, clean, clean |
| Web dependencies | `npm audit --omit=dev` | 0 vulnerabilities |
| Sandbox suites (runc and gVisor) | CI jobs `sandbox`, `sandbox-postgres`, `sandbox-gvisor` | green on `eff4dc7` (CI only; not re-run here) |

The 39 skips are the Docker-backed sandbox tests. They run in CI, under runc and under a
pinned gVisor release. That is **CI-level** evidence only. No deployment host exists, so
gVisor has never been checked on one.

### Research freeze reference

Before any Milestone 3 change, SHA-256 hashes of every research-critical file at `eff4dc7`
were recorded:

- [`milestone-3/research-freeze.sha256`](milestone-3/research-freeze.sha256): 1,515 files.
- [`milestone-3/research-freeze-trees.txt`](milestone-3/research-freeze-trees.txt): the Git
  tree or blob id of each frozen path.

The frozen paths are:

- the diagnosis, evidence, adaptation (policy), learner (BKT), evaluation and content
  (taxonomy, fingerprints, validation) packages;
- `execution/classify.py`, `worker/adapt.py`, `api/recommendation.py` and
  `api/feedback.py`;
- `content/`, `eval/` (held-out, calibration, mutation) and `backend/tests/fixtures/`
  (policy golden files);
- `docs/methodology.md`, `docs/preregistration/`, `docs/evaluation/` and
  `docs/content-design/`.

To verify from the repository root at any later commit:

```
sha256sum -c --quiet docs/reviews/milestone-3/research-freeze.sha256   # silent = unchanged
```

`worker/pipeline.py` is research-adjacent. It runs evidence collection and diagnosis, and
it is also where the D6 failure is handled. It is left out of the frozen set so that the
operational fix can land. Any change to it will be listed line by line in the final report,
with the argument that the change does not alter what is diagnosed or recommended.

## 2. Severity scale

- **P0:** blocks any pilot with real students.
- **P1:** must be fixed or explicitly accepted before the pilot.
- **P2:** should be fixed for a smooth pilot. Workarounds exist.
- **P3:** hygiene, or relevant only at larger scale.

## 3. Findings

Each finding gives its evidence, the files involved, the impact, the planned resolution
and how the resolution will be verified. The stage that resolves it is named, and
**Owner** marks where an owner decision is needed.

### P0

**F01: No deployment host. gVisor has never run on one.**
- Evidence: `docs/deployment.md` begins "nothing is deployed". gVisor is exercised only by
  the `sandbox-gvisor` CI job. ADR-040 makes the production worker refuse to start without
  a registered `runsc`, but no production worker has ever started.
- Files: `docs/deployment.md` §3 and §8; `.github/workflows/ci.yml` (`sandbox-gvisor`).
- Impact: arbitrary student C++ runs on a host whose isolation nobody has checked.
- Resolution: compare architectures (M3.3, **Owner Gate A**). Then, only after the owner
  approves a host and spending, run the sandbox suite with `runsc` on that host and record
  the result (M3.4, **Owner Gate B**).
- Verification: test output from the actual host, labelled host-level. CI and container
  runs never count as host evidence.

**F02: No production image or deployment configuration.**
- Evidence:
  - `backend/Dockerfile` calls itself the development image. It runs as root (no `USER`),
    has no `HEALTHCHECK`, and starts `uvicorn --host 0.0.0.0` with neither
    `--proxy-headers` nor `--forwarded-allow-ips`.
  - There is no production compose file, no reverse proxy or TLS configuration, and no
    example production environment file.
  - Both compose files mount `/var/run/docker.sock` into the worker. They are local-only
    and bound to 127.0.0.1.
- Files: `backend/Dockerfile`, `compose.yaml`, `compose.demo.yaml`.
- Impact: there is nothing reviewable to deploy. If the image were deployed as it is, the
  API would run as root, and behind a proxy every client would share one throttle address.
- Resolution (M3.4):
  - a non-root production image with a health check;
  - a production compose file split into an API side (no Docker) and a worker side;
  - a reverse proxy template with TLS and forwarded-IP settings naming the proxy only;
  - `.env.production.example` with placeholders only.
- Verification: the image builds in CI, `id -u` in the image is not 0, and the config
  refuses to start without its required variables. TLS is **not** claimed until it is
  verified on a host.

**F03: No tested PostgreSQL backup and restore.**
- Evidence: `codeadapt-admin backup` handles SQLite only. `deployment.md` §5 says to run
  `pg_dump` but gives no script, no schedule and no restore procedure, and no restore has
  ever been run.
- Files: `backend/src/codeadapt/auth/cli.py` (`_backup`), `docs/deployment.md` §5.
- Impact: data loss during a pilot cannot be recovered with confidence.
- Resolution (M3.5):
  - a backup script (`pg_dump --format=custom`) and a restore script that restores into
    a fresh database;
  - checks after restore: schema revision, row counts and an integrity query;
  - stated RPO and RTO targets.
- Verification: an actual restore of a populated disposable PostgreSQL database into a
  second disposable database, with the row counts compared. A successful backup command
  alone does not count.

**F04: The pilot has no governance documents and no ethics determination.**
- Evidence: there are no participant information sheet, consent form, data governance or
  retention documents for a pilot. The VAL1-B materials are a different study, and they
  were deferred.
- Impact: real students must not be enrolled.
- Resolution (M3.6): drafts in `docs/pilot/`, with the points that need legal or
  institutional review flagged, including India's DPDP Act 2023. No recruitment. No claim
  of approval. **Owner Gate C** comes before any enrollment.
- Verification: the documents exist, are consistent with what the code actually stores
  (checked against the models), and each one is marked DRAFT, not approved.

### P1

**F05: No readiness probe. The liveness probe proves nothing about dependencies.**
- Evidence: `GET /api/v1/health` always returns `{"status": "ok"}` without touching the
  database (`api/app.py`, `health`). There is no `/ready`. The worker exposes no health
  signal at all.
- Impact: the orchestrator or proxy sends traffic to an API whose database is down or
  unmigrated, and a hung worker goes unnoticed.
- Resolution (M3.2):
  - keep `/health` as liveness;
  - add `GET /api/v1/ready`, which checks that the database answers and that its schema
    revision equals the code's Alembic head (503 otherwise, with no internal detail);
  - the worker writes a heartbeat file on every loop, and a `codeadapt-worker --check`
    command fails when the heartbeat is stale.
- Verification: unit tests for ready, not reachable, and an old schema; a test of the
  heartbeat check; the route stays in the authorization guard's public list on purpose.

**F06 (D6): A failure in adaptation is swallowed.**
- Evidence: `worker/pipeline.py`, `process()`:
  `except Exception: log.exception(...); session.rollback()`. The job is then marked
  DONE with no error. `GET /api/v1/me/recommendation` returns the learner's latest
  recommendation row, which is now the one made for an *earlier* submission.
- Impact: the learner sees a stale recommendation presented as current. The gap shows up
  only in logs, and nobody can count or find the affected submissions.
- Resolution (M3.2), operational part only:
  - record the failure durably (the job keeps state DONE, because the diagnosis
    succeeded, and gets an `adaptation failed: <type>` marker);
  - log a structured event;
  - count the failures in the ops status command.
- This part does not change what is diagnosed or recommended. **Owner:** two follow-ups
  would change learner-facing behaviour, and both wait for an owner decision: hiding the
  stale card ("no recommendation yet") and re-running adaptation later. A later re-run
  would see a different attempt history.
- Verification: a test that forces `adapt()` to raise and asserts the diagnosis is kept,
  the marker is recorded, and no recommendation row is written. The policy golden tests
  stay unchanged.

**F07: Data can leak into logs and the jobs table.**
- Evidence:
  - (a) SQLAlchemy puts bound parameters in exception messages (`[parameters: ...]`). The
    API's unhandled-error handler logs those messages with `exc_info`. The worker logs them
    with `log.exception` and stores `f"{type(exc).__name__}: {exc}"` in `jobs.last_error`.
    Parameters include student source, password hashes and session-token hashes.
  - (b) uvicorn's own access log is on by default. It prints the full request line,
    including the query string, and the client address. `/research/learner-model?username=`
    therefore puts usernames in the log. `deployment.md` §6 says that never happens.
  - (c) Nothing actively redacts secrets. "We never log X" is a convention, not a guard.
- Files: `db/session.py` (`make_engine`), `api/app.py` (`_unhandled`, request logging),
  `worker/pipeline.py`, `backend/Dockerfile` (CMD), `logs.py`.
- Impact: personal data and credential material could end up in log files with no
  retention control.
- Resolution (M3.2):
  - `hide_parameters=True` on every engine;
  - production start command with `--no-access-log`, since the app already logs method,
    path, status and duration without the query string;
  - a redaction filter in `logs.py` that masks database URL passwords, `Cookie` and
    `Set-Cookie` values, CSRF headers and `password=` style pairs in every log record.
- Verification: tests that force an IntegrityError and assert that neither the log line
  nor `last_error` contains the parameter; tests of the redaction filter.

**F08: The worker has no graceful shutdown.**
- Evidence: `worker/main.py` installs no SIGTERM handler. `docker stop` or a deploy kills
  the worker in the middle of a job. The job stays RUNNING until its lease expires (default
  600 s), uses up one of its 3 attempts, and its sandbox containers stay behind until the
  next start-up `reap()`.
- Impact: every restart during a class session delays a student's result by up to 10
  minutes and can push a job towards FAILED.
- Resolution (M3.2): on SIGTERM or SIGINT, stop claiming new jobs, let the current job
  finish within a bounded grace period, then exit 0. Document `stop_grace_period`.
- Verification: a unit test that the loop exits after a stop request and claims nothing
  more.

**F09: No monitoring or alerting.**
- Evidence: the only operational signal is logs (`logs.py`). Nothing measures queue depth,
  the age of the oldest queued job, failed jobs or sandbox unavailability (audit D12).
- Impact: silent failure during a pilot session.
- Resolution (M3.2 and M3.5):
  - `codeadapt-admin status` prints those counts as JSON and exits non-zero when a
    threshold is crossed, so cron or an uptime checker can alert on it;
  - `/ready` serves as the external probe.
- Verification: unit tests for the thresholds; an example cron or uptime setup in the
  runbook.

**F10: A known username can be locked out (audit S6/D10).**
- Evidence: `auth.recent_failures` counts failures per username **or** per client.
  Anyone who knows a username can lock that account out for 15 minutes with 5 bad
  attempts. Behind a proxy without the forwarded-IP setting, all clients share one
  address.
- Impact: denial of login for a targeted student during a session.
- Resolution: the forwarded-IP configuration goes into the M3.4 artifacts. Alternatives
  to lockout and their tradeoffs (per-username delay, per-pair counting, admin unlock) are
  written up in M3.5. **Owner:** no change to the lockout policy without a recorded
  decision, because it has a material impact on users.
- Verification: the existing throttle tests stay unchanged until the decision is made.

**F11: The worker host's Docker socket is root-equivalent.**
- Evidence: the worker drives `docker` through the socket (`execution/docker.py`). Anyone
  who takes over the worker process controls the host, whatever gVisor does for the
  student containers.
- Impact: the worker host must hold nothing else of value. Its only credential should be
  a database role that cannot read auth tables beyond what it needs.
- Resolution: trust boundaries and a least-privilege database role in the M3.3
  architecture document, and a grant script in M3.4.
- Verification: the architecture review, and a test that the worker role cannot read
  `auth_sessions` (on PostgreSQL).

### P2

**F12: The queue stalls on the first submission to each problem (audit D7).**
- Evidence: `pipeline._fingerprints` measures fingerprints under one lock the first time
  each content version is seen in an environment, which takes 1 to 2 minutes per problem.
  There is a single sequential worker loop.
- Resolution (M3.2): a `codeadapt-worker --warm-up` command that measures and stores
  fingerprints for every catalogue version before a session. It calls the existing
  `_fingerprints` code path unchanged, so no research logic changes. Document running two
  workers.
- Verification: a test that warm-up stores one row per version, and that a later
  submission reuses the stored row.

**F13: No retention for operational rows.**
- Evidence: expired or revoked `auth_sessions` rows and `audit_events` rows are never
  deleted, and no retention period exists.
- Resolution: retention periods are set in the M3.6 data governance draft (**Owner**). A
  purge command for expired sessions only, which removes no research data, comes in M3.5.

**F14: No resilience to dropped database connections.**
- Evidence: `make_engine` does not set `pool_pre_ping`. Managed PostgreSQL services close
  idle connections, so the first request after an idle period fails with a 500.
- Resolution (M3.2): `pool_pre_ping=True` for PostgreSQL.
- Verification: a unit test of the engine options.

### P3

**F15: Documentation drift.**
- `deployment.md` §8 says the sandbox pipeline tests run only on SQLite, but CI has a
  `sandbox-postgres` job.
- The `backend/Dockerfile` comment refers to the old "M8" plan.
- Fix both in M3.4.

**F16: Research list correctness and efficiency (audit D8/D9).**
- The outcome filter matches any diagnosis row, and some queries are N+1.
- These are research-reporting code. Leave them out of Milestone 3, because the change
  would touch how researcher metrics are reported. List them in the final report.

**F17: The 5 held problems are visible to students (audit C2).**
- Showing or hiding them is a product decision about content exposure. It is out of
  scope (no content change) and listed for the owner.

## 4. What is already in place (no action)

- Fail-closed configuration (ADR-040): unset `CODEADAPT_ENV` means production, and an
  unknown value is an error.
- Host allow-list, security headers, 1 MiB body limit, and no API docs in production.
- Argon2id passwords, and server-side sessions that store only the token hash.
- CSRF on unsafe methods.
- Session rotation at login, password change, and usernames unique regardless of case
  (ADR-041).
- A 6 × 10 authorization matrix with an anonymous-access guard for every route.
- Sandbox containers run with `--network none`, read-only root, all capabilities dropped,
  `no-new-privileges`, and pids, memory and file limits. They are labelled and reaped.
  The base image is pinned by digest, and the gVisor release is pinned in CI.
- The job queue is fenced against reclaimed claims, and its lease is renewed by a
  heartbeat (ADR-031).

## 5. Proposed implementation sequence

Small commits, each pushed to `claude/project-thread-qk4fuc` with the repo's checks run
first. There will be one PR against `main` at the end. Owner gates stop the stages that
need them. Work that does not depend on a gate continues in the meantime.

1. **M3.2a:** log safety (F07): `hide_parameters`, redaction filter, no uvicorn access
   log in the production command. Tests.
2. **M3.2b:** `/api/v1/ready` and the worker heartbeat and `--check` (F05). DB
   `pool_pre_ping` (F14). Tests.
3. **M3.2c:** D6 operational marker (F06), worker graceful shutdown (F08), warm-up
   command (F12), `codeadapt-admin status` (F09). Tests. Owner decision card for the D6
   learner-facing follow-ups.
4. **M3.3:** architecture comparison, with diagram, trust boundaries, Docker-socket
   analysis and no invented prices. **Owner Gate A** decision card.
5. **M3.4:** production image, production compose, reverse proxy template,
   `.env.production.example`, database role grants, gVisor verification levels, and
   documentation fixes (F02, F11, F15). The image is built in CI. **Owner Gate B** before
   any deployment.
6. **M3.5:** migration safety through 0006 on disposable databases, PostgreSQL backup and
   restore scripts with an actual restore test, RPO and RTO, the session purge, lockout
   alternatives (F03, F10, F13), runbook and incident response.
7. **M3.6:** pilot drafts in `docs/pilot/` (F04). **Owner Gate C**.
8. **M3.7:** full verification, research-freeze hash comparison, PR, and the final report
   with sections A to I.
