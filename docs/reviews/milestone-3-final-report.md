# Milestone 3 final report: pilot operational readiness

**Status: code complete. Infrastructure pending. Pilot authorisation pending.**
Milestone 3 is **not** fully complete. No deployment host has been verified, and there is
no ethics determination or owner Gate A, B or C decision.

- Date: 2026-11-07.
- Scope: the "Milestone 3 master execution prompt" (stages M3.1 to M3.7).

## A. Executive summary

Milestone 3 aimed to make CodeAdapt deployable for a small, ethically approved,
controlled pilot, and to show with evidence how ready it is. It changed no research logic.

### What was achieved (code and documents, verified in CI or with disposable databases)

1. **Baseline audit.** The audit (`milestone-3-baseline-audit.md`) found 17 issues, F01
   to F17: four P0, seven P1, three P2 and three P3.
   - Before any change, 1,515 research-critical files were hashed into a manifest at the
     baseline commit.
2. **Reliability** (ADR-042):
   - Credentials and student source code are kept out of logs and out of `jobs.last_error`.
   - A `/api/v1/ready` probe checks the database and the schema version.
   - The worker stops gracefully, writes a heartbeat file and checks it with `--check`.
   - A `--warm-up` command removes the first-submission stall.
   - Database connections are checked before use.
   - A failed adaptation step is no longer silent (D6). It leaves a visible
     `adaptation failed:` marker.
   - `codeadapt-admin status` reports the queue, failures and the worker's health.
3. **Deployment artifacts.**
   - Non-root production images for the API and the worker, and a Caddy proxy image that
     terminates TLS and sets security headers.
   - Two Compose stacks, one for the App VM and one for the Runner VM, that refuse to
     start without their settings files.
   - Least-privilege PostgreSQL roles. The worker role cannot read accounts, sessions or
     the audit log, and the API role cannot create tables.
   - CI now builds and starts the whole App VM stack behind HTTPS on every push.
4. **Backup and restore.**
   - `pg_dump`/`pg_restore` scripts.
   - An actual restore test on a disposable PostgreSQL database, which compares the
     content of every table before and after.
   - A test that walks every migration step by step: up, down to the base, then up again.
   - A purge command for expired login sessions.
5. **Operations documents:** an architecture comparison, the production runbook, backup
   and restore, incident response, gVisor verification levels, and login-throttle options.
6. **Pilot governance drafts:** the protocol, information sheet, consent form and data
   governance. All are DRAFT and carry DPDP Act 2023 review flags. There is also an
   `erase-learner` command for withdrawal.

### What was not achieved, and why

- **No host exists.** Gates A and B have not been passed, so nothing was provisioned and
  no money was spent. TLS with a real certificate, gVisor on the host, network isolation,
  restore on the host and rollback are all **BLOCKED**.
- **No ethics determination or Gate C.** Recruitment is blocked.
- Some decisions are the owner's: D6 learner-facing behaviour, the login lockout policy,
  retention periods, and F16 and F17. These are listed in section H and were not
  implemented.

CodeAdapt's diagnostic accuracy, learning benefit and educational effectiveness have
**not** been established with real students. Nothing in this milestone changes that.

## B. GitHub information

| Item | Value |
| --- | --- |
| Baseline commit (merged `main`) | `eff4dc7` (PR #3, ADR-041) |
| Feature branch | `claude/project-thread-qk4fuc` |
| Pull request | [#4](https://github.com/rupinderkaur1904/codeadapt/pull/4), open and not merged. The owner merges. |
| Final tested commit | the head of PR #4. Its CI result is recorded on the PR. |

The commits, in order:

| Commit | Stage | Content |
| --- | --- | --- |
| `a3f6d40` | M3.1 | baseline audit and research-freeze manifest |
| `e1aeaff` | M3.2a | log safety: redaction, `hide_parameters`, no access log (F07, F14 logging) |
| `5d83770` | M3.2b | readiness probe, graceful stop, heartbeat, warm-up, status, D6 marker (ADR-042) |
| `c3fd289` | M3.3 | architecture comparison for Gate A |
| `e5e47cc` | M3.4 | production images, App and Runner Compose stacks, TLS proxy, DB roles, CI job |
| `07d807a` | M3.5 | backup and restore with a tested restore, migration walk, session purge, runbook |
| `ab2e838` | M3.6 | pilot documents, `erase-learner` |
| `5554ccb` | M3.7 | CI fix: build the sandbox image before the production-worker gVisor refusal check |
| (this commit) | M3.7 | this report |

## C. Implementation table

| # | Problem (audit) | Files changed | Solution | Tests | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | F07: secrets and source code can reach logs and `jobs.last_error` | `logs.py`, `db/session.py`, `worker/pipeline.py`, `backend/Dockerfile`, `deploy/backend.Dockerfile` | `RedactingFormatter` masks secrets in the message, extras and tracebacks; `hide_parameters=True`; no uvicorn access log; error text redacted and capped at 2,000 characters | `test_logs.py`, `test_operations.py` | PASS (CI and local) |
| 2 | F05: the liveness probe proves nothing | `api/app.py`, `db/migrate.py`, OpenAPI/types | `GET /api/v1/ready`: 200 only when the database answers and the schema is at head, otherwise 503 with no detail. It is public. | `test_operations.py`, authorisation matrix | PASS (CI, through the proxy) |
| 3 | F14: dropped DB connections | `db/session.py` | `pool_pre_ping=True` on PostgreSQL | `test_operations.py` | PASS |
| 4 | F08: no graceful shutdown | `worker/main.py` | SIGTERM/SIGINT finishes the current job and then exits; `stop_grace_period: 120s` | `test_operations.py` | PASS |
| 5 | F09: no worker health | `worker/main.py`, `config.py`, Dockerfile | heartbeat file every 10 s; `--check` fails if it is older than 60 s; Docker health check | `test_operations.py` | PASS. On a host: NOT VERIFIED |
| 6 | F12: first-submission stall | `worker/main.py`, `pipeline.py` | `--warm-up` calls the unchanged fingerprint path for every catalogue version | `test_operations.py` | PASS |
| 7 | F06 / D6: adaptation failure was swallowed | `worker/pipeline.py`, ADR-042 | the job finishes DONE with `last_error = "adaptation failed: ..."`, which `status` counts. The learner-facing behaviour waits for the owner. | `test_operations.py` | PASS for the operational part. Learner-facing part: owner decision |
| 8 | F09: no monitoring | `ops.py`, `auth/cli.py` | `codeadapt-admin status` (exit 1 on problems) and `db-fingerprint` | `test_operations.py` | PASS. External alerting: BLOCKED (no host) |
| 9 | F02: no production image or configuration | `deploy/*`, `.gitignore`, CI | API and worker images (uid 10001), Caddy proxy, `compose.app.yaml`, `compose.runner.yaml`, env examples | CI `production-images` job | PASS in CI on localhost. On a host: BLOCKED |
| 10 | F11: Docker socket is root-equivalent | `db/roles.py`, `auth/cli.py`, architecture doc | worker DB role limited to job tables, denied `users`, `auth_sessions` and `audit_events`; `db-setup` and `db-grants` commands; the worker runs on its own VM | `test_db_roles.py` (PostgreSQL), CI role checks | PASS (role checks). Host separation: BLOCKED |
| 11 | F03: no tested restore | `deploy/backup/*`, `ops.py`, backup doc | dump and restore scripts; restore into a fresh database and compare fingerprints | `test_backup_restore.py` (PostgreSQL) | PASS on a disposable DB. On a host: BLOCKED |
| 12 | Migration safety | `tests/unit/test_migrations.py` | walk every revision up, down to the base, and up again | the same | PASS |
| 13 | F13: no retention for operational rows | `ops.py`, `auth/cli.py` | `purge-sessions` (dry run unless `--apply`) removes expired sessions only | `test_operations.py` | PASS. Periods: owner decision |
| 14 | F10: targeted lockout | `docs/deployment/login-throttle-options.md`, proxy-headers settings | options T0 to T4 analysed, T1+T4 recommended. The policy is **unchanged**. Forwarded-IP handling is configured so that clients are counted separately. | existing throttle tests unchanged | Analysis only. Owner decision |
| 15 | F04: no pilot governance | `docs/pilot/*`, `ops.py`, `auth/cli.py` | DRAFT protocol, information sheet, consent and data governance; `erase-learner` for withdrawal | `test_operations.py` (erase) | Drafts done. Ethics: BLOCKED |
| 16 | F01: gVisor never verified on a host | `docs/deployment/gvisor-verification.md` | levels L1 (CI), L2 (local) and L3 (host), with the L3 procedure | CI `sandbox-gvisor` jobs; production worker refuses to start without runsc | L1 PASS. L3: BLOCKED |
| 17 | F15: documentation drift | `docs/deployment.md`, `backend/Dockerfile` | §8 corrected; probes and monitoring section; stale comment removed | review | PASS |
| 18 | Operations and incident documents | `docs/deployment/*.md` | runbook, backup and restore, incident response, architecture | commands exercised by tests or CI where possible; the rest are marked *proposed* | Documents done. On a host: NOT VERIFIED |
| 19 | CI fix | `.github/workflows/ci.yml` | the gVisor refusal check stopped at "sandbox image missing" before reaching the runtime check, so the image is now built first and the exact refusal message is matched | CI `production-images` | see section D |

## D. Test results

### Local runs (this container, 2026-11-07, at `5554ccb`)

| Command | Result |
| --- | --- |
| `uv run pytest --ignore=tests/sandbox` (SQLite) | **747 passed, 9 skipped.** The 9 skips are PostgreSQL-only tests, which run in the next row. |
| `CODEADAPT_TEST_POSTGRES_URL=... uv run pytest --ignore=tests/sandbox` (PostgreSQL 16) | **756 passed, 0 skipped** |
| `ruff check src tests`; `ruff format --check src tests`; `mypy` | clean: 121 files, no issues |
| `npx vitest run`; `npm run typecheck`; `npm run lint` (web) | **45 passed**; typecheck and lint clean |

- The sandbox suites were **not** run locally. Docker Hub rate limits (429) and slow
  nested Docker make them impractical here, so they run in CI. This is a statement about
  where the tests ran, not a substitute for host verification.
- Before M3.5, a full local run that included the sandbox tests passed 744 tests on both
  SQLite and PostgreSQL.

### CI (GitHub Actions)

- At `e1aeaff`, all 18 jobs passed.
- At `ab2e838` ([run 42365621916](https://github.com/rupinderkaur1904/codeadapt/actions/runs/42365621916)),
  every job passed except `production-images`. These jobs passed:
  - `backend` and `backend-postgres`;
  - `web`, `e2e` and `compose`;
  - every `sandbox (…)` shard;
  - every `sandbox-gvisor (…)` shard. Each runs the sandbox under runsc and checks that
    the production worker starts only under a registered gVisor runtime.
  - `sandbox-postgres` and `sandbox-gvisor (demo-content)` were still running when this
    report was written.
- In `production-images`, the following steps passed:
  - build;
  - the images run as non-root;
  - Compose refuses to start without its settings;
  - the stack starts;
  - HTTPS through the proxy, `/ready` = ready, 401 on `/problems` without login, the
    security headers, the 308 redirect from HTTP to HTTPS, an unknown Host refused, and
    the API container healthy;
  - the database role denials.
- The last step failed only because the sandbox image was missing, so the worker stopped
  before reaching the gVisor check. It did refuse to start, but for the wrong reason.
  `5554ccb` fixes the step. The outcome on the PR head is the authoritative result.

The prompt's checklist mapped to evidence:

- **Backend.** Unit, integration, PostgreSQL, migration, authorisation, authentication,
  production configuration and failure-path tests are all in the suites above. Migration
  coverage is the full walk. The authorisation matrix covers every route.
- **Frontend.** Typecheck, lint, unit tests, the production build, the check that API
  types match the backend, and the Playwright end-to-end test (`e2e`) all run in CI.
- **Sandbox.** The core, resource-limit, timeout and cleanup tests run in the
  `sandbox (…)` and `sandbox-gvisor (…)` jobs. Production runtime rejection is tested in
  `sandbox-gvisor (core)` and `production-images`.

## E. Deployment readiness matrix

- "CI" means verified in GitHub Actions on an ephemeral runner.
- "Host" means a real deployment host. None exists.

| Component | Code / CI | On a host | Notes |
| --- | --- | --- | --- |
| API | PASS | BLOCKED | fails closed, ready probe, headers, Host allow-list |
| Frontend | PASS | BLOCKED | build, e2e, served by Caddy in CI |
| Database (schema, migrations, roles) | PASS | BLOCKED | full migration walk; least-privilege roles checked |
| Sandbox (runc) | PASS | NOT APPLICABLE | production must not use runc |
| Sandbox (gVisor runsc) | PASS (L1) | BLOCKED (L3) | `gvisor-verification.md` L3 procedure |
| Worker lifecycle and health | PASS | BLOCKED | heartbeat, `--check`, graceful stop, warm-up |
| Worker refuses to start without gVisor | PASS in `sandbox-gvisor`. `production-images`: see D | BLOCKED | |
| Reverse proxy | PASS (localhost, internal CA) | BLOCKED | |
| TLS (public certificate) | NOT APPLICABLE in CI | BLOCKED | no domain or host; not claimed operational |
| Network isolation (App and Runner VMs) | design only | BLOCKED | architecture option C |
| Backup | PASS (disposable DB) | BLOCKED | an off-host copy needs a host |
| Restore | PASS (disposable DB, fingerprints equal) | BLOCKED | must be repeated on the host before Gate C |
| Monitoring and alerting | PASS (`status`, probes) | BLOCKED | no external monitor chosen |
| Restart behaviour | PASS (graceful stop test; `restart: unless-stopped`) | NOT VERIFIED | |
| Rollback | documented in the runbook | NOT VERIFIED | image tag rollback plus a restore from backup |
| Pilot consent and governance | drafts PASS (written) | BLOCKED | no ethics determination; Gate C closed |

**Overall: NOT READY for a pilot.** The code is ready for owner review. Every
host-dependent and ethics item is BLOCKED.

## F. Security risks remaining

| Severity | Risk | Mitigation in place | Remaining action | Owner |
| --- | --- | --- | --- | --- |
| High | Student code runs on a host where gVisor has never been verified | worker refuses to start without a registered runsc; L1 CI tests | run the L3 procedure on the Runner VM before any student code | owner (Gate B) |
| High | The Docker socket gives root on the Runner VM | separate VM; worker DB role limited to job tables; no other secrets on that VM | provision as designed; keep the VM single-purpose | owner |
| Medium | Targeted login lockout (F10) | per-client counting behind the proxy; forwarded-IP settings | choose T1+T4 or another option | owner |
| Medium | No external alerting | `status` command, probes | choose an uptime monitor at Gate A | owner |
| Medium | Restore not verified on real infrastructure | restore tested on a disposable DB | restore test on the host before Gate C | owner |
| Medium | Personal data (IP addresses, free-text code) under the DPDP Act | pseudonymous accounts; minimal data; erase command | legal and ethics review of the [REVIEW] items | owner and reviewer |
| Low | Held problems visible to students (F17) | none | product decision | owner |
| Low | Research list N+1 and filter (F16) | researcher-only | research-reporting change, out of scope | owner |

## G. Research freeze verification

- **Manifest.** `docs/reviews/milestone-3/research-freeze.sha256` holds 1,515 files,
  hashed at `eff4dc7` before any change (commit `a3f6d40`).
- **Check.** `sha256sum -c --quiet docs/reviews/milestone-3/research-freeze.sha256`
  passed with no output after every commit, including `5554ccb` and this one.
- **Trees.** `research-freeze-trees.txt` records the git tree hashes of the frozen
  directories.
- **What the freeze covers:** diagnosis, fingerprints, evidence gates, abstention, the
  taxonomy, BKT and its parameters, the recommendation policy, problem content, held-out
  sets, metrics and the evaluation code and data.
- **Code that touches the research pipeline.**
  - `worker/pipeline.py` changed only in how errors are recorded (redaction, the D6
    marker) and in the `warm_up()` entry point. Warm-up calls the unchanged
    `_fingerprints` path.
  - No diagnostic, recommendation or learner-model function changed. This diff was
    reviewed line by line.
- **Results.** The sandbox suites, including held-out evaluation, families, adaptation and
  end to end, pass in CI under both runc and runsc. Their assertions are unchanged.
- **Additions.** No ML model, LLM diagnosis, new concept, new problem or learner-facing
  BKT was added.

## H. Owner decisions still required

1. **Gate A:** architecture (option C recommended), provider, region (an Indian region
   avoids the cross-border question), budget, domain and an uptime monitor.
2. **D6 learner-facing behaviour** when adaptation fails. "Hide the stale card" is
   recommended. There is a decision card.
3. **Gate B:** provisioning and exposure, after the L3 gVisor verification and a host
   restore test pass.
4. **Login throttle policy** (F10): T1+T4 recommended (`login-throttle-options.md`).
5. **Retention periods** (data-governance §6): sessions and logs 30 days, research data
   at most 12 months, backups rolling 30 days. All proposed.
6. **Ethics review body**, and the request for an approval or exemption.
7. **Legal review** of the DPDP [REVIEW] items: notice content, language, age
   confirmation, the s.17 research exemption, breach deadlines and the processor agreement.
8. **Gate C:** enrollment.
9. **F16:** fix the research list filter and its N+1 queries. This changes
   research-reporting code.
10. **F17:** hide or show the five held problems.
11. **Merge PR #4.**

## I. Next steps

### Code complete (in PR #4, pending review and merge)
- Reliability features, deployment artifacts, the backup and restore tooling,
  operational commands, CI checks and all the documents.

### Infrastructure pending (needs Gates A and B; owner action and spending)
1. Provision the App and Runner VMs and PostgreSQL storage in the chosen region.
2. Follow `production-runbook.md`.
3. Run the gVisor L3 verification.
4. Verify TLS with a public certificate.
5. Verify network isolation between the VMs.
6. Run a restore test on the host.
7. Rehearse a rollback.
8. Set up external uptime monitoring.
9. Record each result in the readiness matrix.

### Pilot authorisation pending (Gate C)
1. Choose an ethics body and obtain a written determination.
2. Complete the legal review of the DPDP items.
3. Finalise the documents: fill in the bracketed items, then version and date them.
4. Approve the questionnaire.
5. Obtain the owner's Gate C go-ahead.
6. Only after all of these, recruit participants.
