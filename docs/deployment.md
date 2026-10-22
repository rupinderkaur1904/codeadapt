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
| `CODEADAPT_ENV` | API, worker | `production` (turns off the dev auth stub; Secure cookies; JSON logs) |
| `CODEADAPT_DATABASE_URL` | API, worker | required in production |
| `CODEADAPT_CONTENT_DIR` | API, worker | the content checkout (the real study content lives in a private repo, ADR-009) |
| `CODEADAPT_SANDBOX_RUNTIME` | worker | `runsc` (ADR-003, ADR-028) |
| `CODEADAPT_SANDBOX_MAX_CONCURRENCY` | worker | at most the VM's cores |
| `CODEADAPT_SESSION_HOURS` | API | default 12 |
| `CODEADAPT_SUBMISSIONS_PER_MINUTE` | API | default 10 in production; `none` disables |
| `CODEADAPT_LOG_FORMAT`, `CODEADAPT_LOG_LEVEL` | API, worker | default `json` and `INFO` in production |

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
browser in `X-Request-ID`. Logs never contain source code, passwords or tokens. Security
and researcher-access events go to the `audit_events` table (ADR-029). How long logs and
audit rows are kept is an owner decision (M9).

## 7. Gate checklist (before anyone outside the team can reach it)

- [ ] Sandbox suite passes under `runsc` on the runner VM (step 3).
- [ ] `pip-audit` and `npm audit --omit=dev` are clean (CI).
- [ ] Served over HTTPS only; the reverse proxy sets HSTS; `CODEADAPT_ENV=production`.
- [ ] The reverse proxy passes the real client address, and uvicorn trusts only that
      proxy (`--proxy-headers --forwarded-allow-ips=<proxy>`), so login throttling sees
      clients rather than the proxy.
- [ ] Runner VM egress blocked; API host has no Docker.
- [ ] A backup was taken and a restore tested.
- [ ] Owner approval recorded for exposure (and, for real students, the M9 decisions).

## 8. Not yet verified

- PostgreSQL: the code targets it (ADR-004), but tests run on SQLite only, and the
  Postgres driver is not a dependency yet. A CI job against PostgreSQL is the next M8 step.
- The production container image (the current `backend/Dockerfile` is the dev image).
- gVisor on the real runner VM (CI and the development container only, ADR-028).
