# PR #4 review: the complete Milestone 3 diff

- **Asked by:** the owner, 2026-11-07, before deciding whether to merge.
- **Scope:** every change from `eff4dc7` (merged `main`) to the PR head. The owner asked
  for particular attention to the sandbox, worker, authentication, migration and
  research-critical changes.
- **Reviewer:** Claude, who also wrote this code. This is a self-review, so it is not
  independent. Read it as a careful checklist, not as an external audit.

## Verdict

Four defects were found and fixed during this review, each with a test (section 2). The
owner then decided every open item at Gate B on 2026-11-07, and R5, R6, R7, R8 and R10
are now implemented with regression tests (section 6). Nothing found blocks a merge once
the complete CI pipeline is green on the final head commit. The merge decision is the
owner's.

## 1. What was reviewed, area by area

| Area | What changed | Finding |
| --- | --- | --- |
| **Sandbox** (`execution/`, `sandbox/`) | **Nothing.** No file under `backend/src/codeadapt/execution/` or `sandbox/` changed. | The production guard from ADR-040 is unchanged: the worker refuses to start unless Docker has a registered runsc runtime. It is now also tested in the production image (CI `production-images`). The Runner compose file mounts the Docker socket, which is root-equivalent, and limits the container: read-only filesystem, all capabilities dropped, `no-new-privileges`, uid 10001. gVisor on a real host is still **NOT VERIFIED** (gvisor-verification.md L3). |
| **Worker** (`worker/main.py`, `worker/pipeline.py`) | Graceful SIGTERM stop, heartbeat with `--check`, `--warm-up`, the D6 marker, redacted and bounded error text | Two defects fixed: R2 and R4. Checked as correct: a stop request never interrupts a job; `adaptation_errors` is cleared on every exit path; the job state machine is unchanged (DONE, FAILED, requeue); a requeue on sandbox loss is unchanged. |
| **D6 retry** (`worker/recovery.py`, `api/app.py`) | The owner's decision, implemented today | One defect fixed: R1. Checked: a retry calls the frozen `adapt()` unchanged and only while the failed attempt is the learner's newest; one conditional `UPDATE` claims the retry (tested sequentially, and against a concurrent race on PostgreSQL). |
| **Authentication and authorisation** | No change to login, sessions, CSRF, password hashing or the throttle. New endpoints: `GET /api/v1/ready` (public) and `POST /api/v1/me/recommendation/retry`. New audit kind: `account_erased`. | `/ready` returns only `ready` or `not-ready`, with no detail. The retry needs a session and that session's CSRF token, and acts only on the caller's own attempts (tested in the authorisation matrix, including an unknown role). The test that every non-public route needs a login still passes. |
| **Migrations** | **No new migration.** `models.py` and `backend/migrations/` are unchanged. | A new test walks every revision up, down to the base, and up again. In production, migrations run as the schema owner, and the app and worker use the least-privilege roles. |
| **Database roles** (`db/roles.py`) | Grants for the API and worker roles; `db-setup` | Correct for the worker: it is denied `users`, `auth_sessions` and `audit_events` (tested on PostgreSQL and in CI). One item open: R7. |
| **Logging** (`logs.py`, `db/session.py`) | Redaction, `hide_parameters`, no access log | Correct for application logs. One item open: R8. |
| **Operations** (`ops.py`, `auth/cli.py`) | `status`, `db-fingerprint`, `purge-sessions`, `erase-learner`, `db-setup` | One defect fixed: R3. `purge-sessions` and `erase-learner` are dry runs unless `--apply`. |
| **Deployment files** (`deploy/`) | Images, two Compose stacks, Caddy, backup scripts | Two items open: R5 and R6. |
| **CI** (`.github/workflows/ci.yml`) | A new `production-images` job | Additions only: no existing job, step or test was removed or weakened. Fixed earlier (`5554ccb`): the gVisor-refusal step stopped at a missing image instead of reaching the gVisor check. |
| **Tests** | New tests, and three existing files adjusted | The only existing assertions that changed are in `test_trajectories.py`. They check the shape of the learner response, which now includes the owner-approved `adaptation_unavailable` flag. The checks that no learner-model or BKT text reaches students are unchanged. |
| **Research-critical** | — | See section 4. |

## 2. Defects found and fixed (commit `d5630db`)

| # | Severity | Problem | Fix | Test |
| --- | --- | --- | --- | --- |
| R1 | Medium (research consistency) | The API's D6 retry built `PolicyV1()` with its default version, while the worker uses `CODEADAPT_POLICY_VERSION`. If that setting ever changed, a recovered recommendation would come from a different policy version than every other recommendation. | The API now builds the same policy as the worker. | `test_api_shows_the_fallback_then_recovers_on_retry` checks the stored `policy_version`. |
| R2 | Medium (learner-facing) | If a worker died between committing the diagnosis and committing the adaptation (for example after a kill or out-of-memory), the redelivered job was finished DONE with no marker. The learner then silently kept a recommendation that predated their attempt, which is exactly what D6 is meant to prevent. | A redelivered job that has a diagnosis but no adaptation output is finished with the D6 marker, so the learner sees the fallback message and can retry. | Two new tests in `test_pipeline_redelivery.py`, covering the marked case and the unmarked case. |
| R3 | Medium (privacy, withdrawal) | `erase-learner` removed every audit row carrying the learner's name. However, a researcher's access record stores the path and query, for example `learner-model?username=p017`, or a trace path containing the learner's submission id. These records survived the erasure. | The researcher's access records are kept, because they show access control was followed, but any target that names the learner gets `(erased learner)`. Other learners' records are untouched. The dry run reports `audit_events_scrubbed`. | The erase test now covers both kinds of target and one record that must be kept. |
| R4 | Low (operations) | If the heartbeat file could not be written, the heartbeat task died. When the worker then stopped, the task's exception could replace the worker's normal exit. | The worker logs a warning and keeps going. The stale file still makes the health check fail. | `test_heartbeat_task_survives_an_unwritable_file` |

## 3. Items proposed for Gate B (all decided; see section 6 for what was done)

| # | Severity | Item | Proposal | Who decides |
| --- | --- | --- | --- | --- |
| R5 | Medium | The worker's connection to PostgreSQL crosses the private network between the two VMs **without TLS**. The password is protected by SCRAM, but submissions and diagnoses travel in clear text on that network. data-governance.md now says so. | Before enrollment: give PostgreSQL a server certificate from a small private CA and set `sslmode=verify-full` on the worker. This is about 20 lines of configuration plus a runbook step, and needs testing on the host. | Owner, at Gate B |
| R6 | Low | Base images are pinned by tag only, not by digest: `python:3.13-slim`, `docker:29-cli`, `caddy:2.8.4-alpine`, `postgres:16.4-alpine`, `node`. A re-pushed tag would change what gets built. | Pin each image to an `@sha256:` digest when the first production images are built, and record the digests in the runbook. | Routine; at Gate B |
| R7 | Low | The API database role can `UPDATE` and `DELETE` on every table, including `audit_events` and `alembic_version`. A compromised API process could erase the access log. | Revoke `UPDATE` and `DELETE` on `audit_events` from the API role, and all writes on `alembic_version`. Run `erase-learner` and `purge-sessions` with the owner connection, as `db-setup` already does. This changes the runbook and the scope of an existing security role, so it needs your approval. | Owner |
| R8 | Low | Uvicorn's own `uvicorn.error` logger has its own handler, so it does not go through the redacting formatter. The risk is small: the app catches every exception itself and logs it through the redacting logger, so uvicorn logs mostly start-up and shutdown messages. | Start uvicorn with `--log-config` pointing at the redacting formatter. | Routine |
| R9 | Info | `stop_grace_period: 120s` can be shorter than a first-time fingerprint measurement (1–2 min). | Already handled: run `codeadapt-worker --warm-up` before each session (runbook §5). A job killed anyway is recovered through its lease (ADR-031). | — |
| R10 | Info (D6 limitation) | Suppose an attempt's adaptation fails, and the learner's next attempt gives no adaptation output (for example a compile error). The fallback message then stays, and "Try again" is refused, because re-running the older attempt would use a history the policy never saw. The fallback clears at the next attempt that has test results. | Accept for the pilot, or change the message so it suggests submitting again. Changing the message is a product decision. | Owner |

## 4. Research freeze

- `sha256sum -c --quiet docs/reviews/milestone-3/research-freeze.sha256` passes at
  `d5630db`. All 1,515 files are unchanged.
- No file changed in any of these:
  - `adaptation/`, `diagnosis/`, `evidence/`, `learner/`, `content/`;
  - `worker/adapt.py`, `api/recommendation.py`, `api/feedback.py`;
  - the migrations;
  - `content/` or the held-out sets.
- `worker/pipeline.py` changes only how errors are recorded, the `warm_up()` entry point,
  and the redelivery marker (R2). Diagnosis, fingerprints and evidence code paths are
  byte-for-byte the same.
- The D6 retry calls the frozen `adapt()` with the same submission, diagnosis, catalogue
  and policy version. Only the time at which a recovered recommendation is stored differs.
  The learner-facing behaviour was the owner's decision on 2026-11-07.

## 5. Test evidence at `d5630db` (local)

| Suite | Result |
| --- | --- |
| Backend, SQLite, excluding sandbox | 757 passed, 10 skipped (PostgreSQL-only tests) |
| Backend, PostgreSQL 16, excluding sandbox | 767 passed |
| `ruff check`, `ruff format --check`, `mypy` | clean (123 files) |
| Web: vitest, typecheck, lint, format | 47 passed; clean |

The sandbox, gVisor, end-to-end and production-image suites run in CI on the PR. Their
result on the head commit is the one that counts.

## 6. Gate B decisions (owner, 2026-11-07) and what was done

The owner reviewed this document and decided every open item. Each change is limited to
the approved operational scope: no change to sandbox execution, research algorithms,
migrations, recommendation policy, diagnosis or evaluation. The research-freeze check
passes after every commit.

| # | Owner decision | Commit | What changed | Regression tests |
| --- | --- | --- | --- | --- |
| R10 | Two messages; "Try again" only when a retry is valid | `14f2539` | The learner response gains `retry_available`, true only while a failure is pending and no newer attempt exists. With it: "We couldn't prepare your next recommended problem. You can try again, or submit another solution." and the button. Without it: "We couldn't prepare your next recommended problem. Your previous work is saved. Submit another solution to continue." and no button. | Backend: availability follows the newest attempt; the API offers no retry after a newer attempt, and a retry sent anyway changes nothing. Web: each message, and the button only when valid. |
| R7 | Revoke audit rewrites and schema-revision writes from the API role | `26c9864` | `db-setup` revokes `UPDATE`, `DELETE` and `TRUNCATE` on `audit_events`, and every write on `alembic_version`, from the API role. `erase-learner` and `purge-sessions` run as the schema owner through a new one-off `admin` Compose service (runbook §4b). Run from the API container, `erase-learner` stops with a message pointing there. | PostgreSQL: the API role can insert and read audit rows but not change, delete or truncate them; it can read but not write the schema revision; login, failed login, logout and `/ready` still work under it; erasure fails as the API role and works through the owner connection. CI checks the same grants on the production stack. |
| R8 | Route uvicorn's logs through the redacting configuration | `a9dc660` | The API image starts uvicorn with `--log-config codeadapt/uvicorn_logging.json`, which puts the application's redacting handler on the root logger and makes uvicorn's loggers use it. | A real uvicorn whose start-up fails with a database URL, a password and a session cookie in the error: without the config all three leak (control); with it none do, the event is still logged as JSON, and the traceback is masked. One handler only; the image uses the config. |
| R6 | Pin production images by SHA-256 digest; record them in the runbook | `df01a67` | `python`, `docker` CLI, `node`, `caddy` and `postgres` pinned to multi-platform digests (amd64 and arm64), looked up on 2026-11-07. Runbook §0a lists them with the update procedure. The GCC pin is unchanged (research freeze). | Every external image in `deploy/` and `sandbox/` must carry a digest, and every digest must be in the runbook. |
| R5 | PostgreSQL TLS from a private CA; worker `verify-full`; test valid and invalid certificates | `01ecf11` | `deploy/db-tls/make-db-certs.sh` (private CA, server certificate for `db.codeadapt.internal` and `db`); PostgreSQL with `ssl=on`, TLS 1.2 or later, and a `pg_hba.conf` that refuses TCP without TLS; every database URL uses `sslmode=verify-full`; the production worker refuses to start without it. | Unit: the worker guard (no TLS, `require`, `verify-ca`, missing CA all refused) and the certificate script. CI, against the production Compose stack as the worker role: a valid certificate connects over TLS 1.2+; another CA's certificate, another name, an address instead of the name, and plain text are all refused. |

**Still not verified, and not claimed:**

- TLS, gVisor and the network rules on a real host. The runbook lists the host checks
  (§1 step 8, §2 steps 6 and 10). CI runs the production images on one machine, which is
  evidence about the configuration, not about a host.
- An expired server certificate is not tested. libpq refuses one under `verify-full`, as
  it does an unknown CA. The runbook says to issue the next certificate before 397 days.
- The `admin` service and the TLS settings change the runbook. The owner should read
  §0a, §1 step 5, §2 steps 5 and 10, and §4b before provisioning.
