# Deployment guide (M8, draft)

Status: **nothing is deployed.** This page describes how a deployment must be set up
once the owner decides on hosting (an open owner question, roadmap M8/M9). No real
student may use any deployment before the M8 gate below passes **and** the owner records
the M9 decisions (ethics determination, consent, cohort, data retention).

## 1. Topology

```
 browser ──HTTPS──> reverse proxy (TLS) ──> API host: uvicorn (codeadapt.api)
                                             │  holds DB credentials only; no Docker
                                             ▼
                                         PostgreSQL 16 ◀── runner VM: codeadapt-worker
                                                            Docker + gVisor (runsc),
                                                            egress firewalled
```

- The API host never runs Docker and never holds the Docker socket (security.md §2).
- The worker runs on a separate VM whose only secret is its database role. The Docker
  socket on that VM is root-equivalent, which is why nothing else lives there.
- The web app is a static build (`npm run build`, `web/dist/`) served by the reverse proxy;
  `/api` is proxied to uvicorn on the same origin, so cookies stay same-site.

## 2. Configuration

| Variable | Where | Value |
| --- | --- | --- |
| `CODEADAPT_ENV` | API, worker | `production` (turns off the dev auth stub; Secure cookies; JSON logs). Unset also means production; any value other than `dev`, `test`, `production` stops start-up (ADR-040) |
| `CODEADAPT_DATABASE_URL` | API, worker | required in production |
| `CODEADAPT_ALLOWED_HOSTS` | API | required in production: comma-separated host names the API is served under (no `*`); other `Host` headers get 400 (ADR-040) |
| `CODEADAPT_CONTENT_DIR` | API, worker | the content checkout (the real study content lives in a private repo, ADR-009) |
| `CODEADAPT_SANDBOX_RUNTIME` | worker | `runsc` (ADR-003, ADR-028). In production the worker refuses to start unless this names a `runsc` runtime registered with Docker (ADR-040) |
| `CODEADAPT_SANDBOX_ALLOW_RUNC` | worker | leave **unset**. `local-demo-only` lets a production-mode worker use runc, for compose.demo.yaml only |
| `CODEADAPT_SANDBOX_MAX_CONCURRENCY` | worker | at most the VM's cores |
| `CODEADAPT_SESSION_HOURS` | API | default 12 |
| `CODEADAPT_SUBMISSIONS_PER_MINUTE` | API | default 10 in production; `none` disables |
| `CODEADAPT_SIGNUP` | API | leave **unset** (sign-up off). `invite-code` shows "Create an account" on the login page; new accounts need an invite code from `codeadapt-admin invite-create` and are students with data class `dev` (ADR-044). Any other value stops start-up |
| `CODEADAPT_SIGNUPS_PER_CLIENT_PER_HOUR` | API | default 40 successful sign-ups per client address per hour |
| `CODEADAPT_POLICY_VERSION` | worker | recommendation policy, `1.5` (default) or `1.4` (ADR-038) |
| `CODEADAPT_LOG_FORMAT`, `CODEADAPT_LOG_LEVEL` | API, worker | default `json` and `INFO` in production |
| `CODEADAPT_WORKER_HEARTBEAT_FILE` | worker | e.g. `/tmp/codeadapt-worker.heartbeat`; enables `codeadapt-worker --check` as the container health check (ADR-042) |

## 3. Runner VM

1. Install Docker and gVisor from a pinned release with its checksum verified, exactly as
   the `sandbox-gvisor` CI job does, then `runsc install` and restart Docker.
2. `docker build -t codeadapt-sandbox:gcc14.2-1 sandbox/`.
3. Run the sandbox suite on this VM:
   `CODEADAPT_SANDBOX_RUNTIME=runsc CODEADAPT_REQUIRE_SANDBOX=1 uv run pytest tests/sandbox`.
   Record the result in docs/development.md. This is the M8 gate (security.md §6).
4. Block all egress from the VM except to the database.

## 4. Accounts

There is no sign-up. Create accounts with an explicit role and data class:

```
uv run codeadapt-admin create-user <username> --role student --data-class real
uv run codeadapt-admin set-password <username>
uv run codeadapt-admin disable <username>
uv run codeadapt-admin list
```

The password is read without echo, or as one line on stdin. Real-student accounts
(`--data-class real`) must not be created before the M9 consent process exists.

## 5. Backups

- SQLite (single-host pilots only): `uv run codeadapt-admin backup <file>` takes a
  consistent copy while the API and worker run, then checks its integrity and reports the
  schema revision.
- PostgreSQL: `pg_dump --format=custom`, on a schedule, to storage outside the database
  host. Test a restore before relying on it.
- Backups contain submissions and, for real accounts, personal data. They follow the
  data-handling rules the owner sets for M9.

## 6. Logs and audit

The API and worker write one JSON object per line to stderr: request method, path (never
the query string), status, duration and request id. The same id is returned to the
browser in `X-Request-ID`. Logs never contain source code, passwords or tokens: database
errors carry no bound values, every record passes a redaction filter, and uvicorn must run
with `--no-access-log` (its access log prints query strings and client addresses) (ADR-042).

Probes and monitoring (ADR-042):

- `GET /api/v1/health`: liveness. `GET /api/v1/ready`: 200 only when the database answers
  and its schema is at the code's migration head.
- `codeadapt-worker --check`: worker health from its heartbeat file.
- `codeadapt-admin status`: queue depth, oldest queued age, lost workers, failed jobs and
  adaptation failures as JSON; exit 1 when a threshold is crossed. Run it from cron every
  few minutes and alert on a non-zero exit.
- `codeadapt-worker --warm-up` before a class session measures every problem's
  fingerprints, so the first submission to a problem does not wait 1-2 minutes.
- Stop the worker with SIGTERM and a grace period of at least 120 s: it finishes the
  current job and claims no more. Security
and researcher-access events go to the `audit_events` table (ADR-029). How long logs and
audit rows are kept is an owner decision (M9).

## 7. Gate checklist (before anyone outside the team can reach it)

- [ ] Sandbox suite passes under `runsc` on the runner VM (step 3).
- [ ] `pip-audit` and `npm audit --omit=dev` are clean (CI).
- [ ] Served over HTTPS only; the reverse proxy sets HSTS; `CODEADAPT_ENV=production`.
- [ ] The reverse proxy passes the real client address, and uvicorn trusts only that
      proxy (`--proxy-headers --forwarded-allow-ips=<proxy>`), so login throttling sees
      clients rather than the proxy. Never `--forwarded-allow-ips='*'`: any client could then
      choose its own address and escape the per-client throttle.
- [ ] The reverse proxy forwards the original `Host`, and that name is in
      `CODEADAPT_ALLOWED_HOSTS`. It serves the static web build with its own headers (at
      least `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, a CSP that allows the
      app's own scripts and styles); the API adds its own headers to `/api` responses (ADR-040).
- [ ] Runner VM egress blocked; API host has no Docker.
- [ ] A backup was taken and a restore tested.
- [ ] Owner approval recorded for exposure (and, for real students, the M9 decisions).

## 8. Not yet verified

- PostgreSQL: the driver (psycopg 3) is a dependency; the `backend-postgres` CI job runs
  every non-sandbox test against PostgreSQL 16, and `sandbox-postgres` runs the sandbox
  pipeline against it, each on a freshly migrated database.
- Production images, compose files, reverse proxy and database roles now exist in
  `deploy/` (Milestone 3, ADR-042) and are built and smoke-tested in the
  `production-images` CI job. That is CI-level evidence: TLS uses Caddy's internal CA for
  `localhost` there. TLS with a real certificate is not verified until it runs on a host.
- gVisor on the real runner VM: see `docs/deployment/gvisor-verification.md` (levels L1-L3;
  L3, the host, is not verified).
