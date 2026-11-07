# CodeAdapt Milestone 2: security report (2026-11-06)

PRs (both open, **not merged**; merge #1 first):
- PR #1 https://github.com/rupinderkaur1904/codeadapt/pull/1 (`claude/project-thread-qk4fuc`): `3598c4b` hardening (ADR-040), `e35f6c3` CI production-worker check. **CI green: 18/18 jobs on e35f6c3** (three runs, 54 successful check runs).
- PR #3 https://github.com/rupinderkaur1904/codeadapt/pull/3 (`claude/project-thread-qk4fuc-auth-parity`, stacked on #1): `4786982` usernames/rotation/password change (ADR-041), `3a5c3d4` web Account page + docs, `6ab2754` e2e locator fix. **CI green: 18/18 jobs on 6ab2754** (two runs).
- PR #2 was opened by mistake from the Claude Code UI (main into an old branch) and closed unmerged at the owner's request.

## 0. Every change, and why

| # | Change | Where | Why |
| --- | --- | --- | --- |
| 1 | Unset or blank `CODEADAPT_ENV` now means production; unknown values stop start-up | `config.py` (PR #1) | Audit D4: the old default was `dev`, so a deployment that forgot the variable let anyone act as a researcher via `X-Dev-Role`. Fail closed. |
| 2 | Production API refuses to start without `CODEADAPT_ALLOWED_HOSTS` (and refuses `*`); Host allow-list via `TrustedHostMiddleware` | `config.py`, `api/app.py` (PR #1) | Stops Host-header abuse; misconfiguration is a clear start-up error naming the variable, never a value. |
| 3 | Security headers on every API response (nosniff, frame DENY, no-referrer, no-store, CORP, `default-src 'none'` CSP); HSTS in production | `api/security.py` (PR #1) | The API returns private learner data: no caching, no framing, no content sniffing. |
| 4 | No `/api/docs`, `/api/redoc`, `/api/openapi.json` in production | `api/app.py` (PR #1) | Information disclosure; docs stay in dev/test. |
| 5 | Request bodies over 1 MiB get 413 (including chunked bodies) | `api/security.py` (PR #1) | Memory exhaustion via large bodies; submissions are 64 KiB at most anyway. |
| 6 | Accounts with an unknown role get 403 everywhere | `api/app.py` (PR #1) | Deny by default: a typo'd or future role used to be treated as a student. |
| 7 | Production worker refuses to start unless `CODEADAPT_SANDBOX_RUNTIME` names a registered `runsc`; only logged `CODEADAPT_SANDBOX_ALLOW_RUNC=local-demo-only` (demo compose) is exempt | `worker/main.py`, `execution/docker.py`, `compose.demo.yaml` (PR #1) | Audit D5: student C++ ran under runc when the variable was unset. Explicit `--runtime` means no silent fallback. |
| 8 | CI step: production worker starts under runsc, refuses runc and an unregistered runtime | `.github/workflows/ci.yml` (PR #1) | Proves rule 7 against real gVisor on every PR. |
| 9 | `codeadapt-openapi` builds with fixed test settings | `api/openapi_export.py` (PR #1) | It used `Settings.from_env()`, which now (rightly) fails without production config. |
| 10 | Table-driven authorization/IDOR tests (6 principals × 10 endpoints) plus a guard that any new `/api` route must refuse anonymous callers | `tests/unit/test_authorization_matrix.py` (PR #1) | Milestone requirement; makes accidental future bypasses fail CI. |
| 11 | Config/headers/host/body/runtime tests | `tests/unit/test_production_hardening.py` (PR #1) | Regression tests for items 1–7. |
| 12 | Docs: ADR-040, security.md, deployment.md (new variables, proxy rules), development.md (`export CODEADAPT_ENV=dev`), demo script | `docs/` (PR #1) | Local runs now need an explicit dev setting; deployers need the new variables and proxy rules. |
| 13 | Migration 0006: unique index on `lower(username)`; stops and lists any existing collisions; downgrade drops it | `migrations/versions/0006_…` (PR #3) | "Alice" and "alice" could be two accounts (shadow accounts, confusing research views). Enforced by the database, so concurrent creation cannot race it. |
| 14 | Login, `codeadapt-admin` and learner-model lookup compare `lower()` on both sides; throttle ignores case | `auth/__init__.py`, `auth/cli.py`, `api/app.py` (PR #3) | Lookups must agree with the index; changing case must not reset the lockout counter. |
| 15 | Login revokes the browser's previous session before issuing a new one | `api/app.py` (PR #3) | Session hygiene (no leftover live session when someone logs in on a shared machine). |
| 16 | `POST /api/v1/auth/password` (current password + CSRF; ends every session; new session for this browser; failures audited and throttled) | `api/app.py`, `api/schemas.py` (PR #3) | No self-service change existed; a leaked password could not be changed by its owner without an operator. |
| 17 | Web Account page (click your username) | `web/src/pages/AccountPage.tsx`, `App.tsx`, `api/client.ts` (PR #3) | UI for item 16; switches to the new CSRF token after the change. |
| 18 | e2e locator for the Research link made exact | `web/e2e/login.spec.ts` (PR #3) | The new account link's text "e2e-researcher" also matched "Research". |
| 19 | Tests for 13–17 | `tests/unit/test_auth_parity.py`, `AccountPage.test.tsx` (PR #3) | Migration up/down/collision, case-insensitivity, rotation, password-change paths. |
| 20 | Docs: ADR-041, security.md | `docs/` (PR #3) | Record of the decisions. |

Not changed anywhere: diagnosis v1.3, recommendation policy 1.5, evidence, skill attribution, learner model/BKT parameters, content, evaluation fixtures, migrations 0001–0005.

## 1. Executive summary

- **The original `edygvs` auth branch was not recovered.** It is not on GitHub, and the owner chose to use GitHub only, not the laptop folder. Nothing was recreated from its documentation.
- On the owner's choice ("Fresh hardening on main"), this milestone fixed the two critical audit findings in the code that is on GitHub:
  - **D4:** dev auth could be reached through a missing environment variable.
  - **D5:** a production worker accepted runc.
- It also added a Host allow-list, security headers, a body limit, docs-off in production, deny-by-default for unknown roles, and a table-driven authorization/IDOR test suite.
- No migration was added. The research pipeline is untouched.
- Features that existed only on edygvs are still missing: DB-level case-insensitive usernames (migration 0006), self-service password change, session rotation at login, and `/ready`.

## 2. Initial Git state (cloud clone of GitHub)

- Path: `/home/user/codeadapt`. Branch: `claude/project-thread-qk4fuc` at `0cf805a`, which equals `origin/main`. The working tree was clean.
- Remote: `origin https://github.com/rupinderkaur1904/codeadapt`.
- Remote branches: `main`, `claude/project-thread-{0tqp29, 9vflva, ce2sv5, cezsmq, dyivyy, jn9de7, qk4fuc, zyjfh1}`. There is **no `edygvs`**, and `git ls-remote` finds no match.
- Local branches: `cezsmq` (tracks origin, `52124a4`) and `qk4fuc`.
- The laptop folder was not used, at the owner's instruction ("I want you to totally rely on the GitHub", 2026-11-06 16:57).

## 3. Recovery of `edygvs`

**Not recovered.** The recovery operation stopped, as the brief requires. The 2026-10-27 report says the branch was cut from `dyivyy` `a5dd064` on Windows 11 and never pushed. It may still exist in the laptop clone. If it is pushed later, it should be compared with this PR rather than merged blindly, because both touch `config.py`, `api/app.py` and the worker.

## 4. Branch ancestry

`qk4fuc` = `main` (`0cf805a`) + `3598c4b` + `e35f6c3`. It fast-forwards from main, with no rebase, no force-push and no history rewrite.

## 5. Authentication architecture (as on main, verified in code)

- Passwords are hashed with Argon2id (argon2-cffi defaults) with a minimum of 12 characters. Unknown usernames are verified against a dummy hash, so a miss takes the same time as a hit. Hashes are upgraded on login when the parameters change.
- Sessions are server-side. The token comes from `secrets.token_urlsafe(32)`, and only its SHA-256 is stored.
- The cookie is `codeadapt_session` with HttpOnly, SameSite=Strict and Path=/api, plus Secure in production.
- Each session has its own CSRF token, which every non-GET/HEAD/OPTIONS request must send in `X-CSRF-Token` (compared in constant time).
- Expiry is enforced server-side (12 h default). Logout revokes the server row. `codeadapt-admin disable` and `set-password` revoke all of the user's sessions.
- There is an append-only audit log of logins, failures, throttles, researcher access and staff views of other users' submissions.
- Accounts are created by an operator only. There is no self-registration.

## 6. Password and session review

| Check | Result |
| --- | --- |
| No plaintext storage | Verified (Argon2id hash only) |
| Uniform failure message | Verified: "Wrong username or password" for both an unknown user and a wrong password |
| Server-side validation | Length is enforced in `hash_password`; the login body is capped at 1024 characters |
| Password change verifies the old password | **Not applicable: there is no self-service change on main.** Only the operator CLI exists, and it revokes sessions. |
| Session fixation | Tokens are only ever generated by the server, and login always issues a new token, so a planted token cannot be adopted. However, a session that was already live is **not revoked** at login (rotation was an edygvs feature). This is a low risk. |
| Logout invalidates the server session | Verified (`revoked_at`); the existing tests cover it |
| Expiry enforced | Verified in `resolve_session` |
| CSRF on state-changing requests | Verified. A new test shows another session's CSRF token is refused (403). |

## 7. Authorization permission matrix (actual roles: student, researcher, admin)

Anonymous callers get 401 on everything except `POST /auth/login` and `GET /health`.

| Endpoint | Owner student | Other student | Researcher | Admin | Unknown role |
| --- | --- | --- | --- | --- | --- |
| `GET /submissions/{id}` | 200 | **404** | 200 (audited) | 200 (audited) | 403 |
| `GET /research/submissions/{id}/trace` | 403 | 403 | 200 | 200 | 403 |
| `GET /research/learner-model?username=` | 403 | 403 | 200 | 200 | 403 |
| `GET /research/submissions`, `/research/metrics` | 403 | 403 | 200 | 200 | 403 |
| `GET /submissions`, `/me/recommendation`, `/problems`, `/auth/me` | own only | own only | own only | own only | 403 |

Researchers and admins have the same permissions. The code has no admin-only API; admin operations live in the CLI and need database credentials. The unknown-role column changed in this milestone: before, such accounts were treated as students.

## 8. IDOR test results

`tests/unit/test_authorization_matrix.py` runs in production mode with real password sessions. It covers:

- all 10 rows of the matrix above, including a non-existent submission ID;
- list isolation (another student's list does not include the owner's submission);
- extra-field injection (`user_id`), which is rejected with 422;
- cross-session CSRF, refused with 403;
- `X-Dev-Role: researcher` next to a student session, which has no effect;
- a guard that every `/api` route except login and health returns 401 to anonymous callers.

All 14 tests pass on SQLite and on PostgreSQL 16. No IDOR was found. Students get 404 for other students' submissions, so the existence of an ID is not revealed.

## 9. Production configuration hardening (D4)

- An unset or blank `CODEADAPT_ENV` now means production.
- Values such as `development`, `DEV` or `staging` stop start-up with "CODEADAPT_ENV must be one of: dev, test, production".
- When `CODEADAPT_DATABASE_URL` is missing, the error says so and hints that `CODEADAPT_ENV` is unset.
- The API refuses to start in production without `CODEADAPT_ALLOWED_HOSTS`, or if it contains `*`.
- Error messages never include values; a test checks that a password in the database URL is not echoed.
- `X-Dev-Role` is ignored in production rather than refused, because the web client sends it on every request. It cannot select an identity or raise privileges. A test proves this.
- Compose: `compose.yaml` sets `dev` explicitly. `compose.demo.yaml` sets production plus `CODEADAPT_ALLOWED_HOSTS=localhost,127.0.0.1,api` and the runc demo override. `web/e2e/backend.sh` sets `test`. Local instructions in docs/development.md now export `CODEADAPT_ENV=dev`.

## 10. gVisor enforcement (D5)

- `require_production_runtime` runs at worker start-up. In production it requires `CODEADAPT_SANDBOX_RUNTIME` to name a `runsc*` runtime, and that runtime must appear in `docker info .Runtimes`. Otherwise the worker exits with a clear error.
- Each container gets an explicit `--runtime runsc`. If gVisor disappears later, the run fails as an infrastructure error and there is no fallback.
- The only exception is `CODEADAPT_SANDBOX_ALLOW_RUNC=local-demo-only`. It writes a loud warning log, any other value is a config error, and it is used only by the local login-mode demo.
- Dev and test behaviour is unchanged. CI still runs the full sandbox suite under both runc and runsc. Runtime provenance (`EnvironmentInfo.container_runtime`) is unchanged.
- Isolation flags (`_hardening`) were not modified.
- Checked by hand against a real Docker daemon: runc was refused, `runsc-missing` was refused, and the override was allowed with the warning.
- **Not production-verified.** gVisor on a real deployment host is a separate step.

## 11. Host validation and security headers

- Host: Starlette `TrustedHostMiddleware` with the allow-list, in production only. A bad Host gets 400, and that response still carries the security headers.
- Headers on every API response, including 404s and errors: `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, `Cross-Origin-Resource-Policy: same-origin`, and CSP `default-src 'none'; frame-ancestors 'none'`. The dev-only docs pages are exempt from the CSP. Production adds HSTS (`max-age=31536000`).
- The web build's headers must come from the reverse proxy (docs/deployment.md §7).
- CORS: there is no CORS middleware, so cross-origin browser calls are refused. The app is same-origin behind the proxy.
- OpenAPI and docs are off in production.
- Body limit: 1 MiB, counted as the body arrives, so it covers chunked bodies too. Submissions are separately capped at 64 KiB.
- Errors: unhandled exceptions return a generic 500 problem+json with a request ID, and the detail goes only to the log.
- Forwarded headers: uvicorn trusts `X-Forwarded-For` only from `--forwarded-allow-ips`. The deployment checklist now forbids `*`.

## 12. Migration review

There is **no migration 0006 on GitHub**; it was on edygvs. The chain is 0001 to 0005 and was not modified. Every one of the 704 backend tests migrates a fresh database to head, on SQLite and on PostgreSQL 16, and all passed locally. Upgrading a populated 0005 database is not affected because no schema changed.

**Proposed for a future milestone (not applied):** a new migration 0006 adding a unique index on `lower(username)`. It should first check for and list colliding names, and its downgrade should drop the index. In this milestone, `codeadapt-admin` refuses case-only duplicates instead. That check is operator-side only and is not safe against two operators creating accounts at the same moment.

## 13. Testing results (local, Linux container)

| Suite | Before (main) | After |
| --- | --- | --- |
| Backend non-sandbox, SQLite | 666 passed | **704 passed** |
| Backend non-sandbox, PostgreSQL 16 | not run | **704 passed** |
| ruff check, ruff format --check, mypy (strict) | clean | clean |
| OpenAPI and web types regenerated | — | no diff |
| Web lint, typecheck, vitest | 43 passed | 43 passed (no web code changed) |
| Production worker refusals (real Docker, runc host) | — | refused runc; refused unregistered runsc; demo override warned |

Not run locally: the sandbox suites (runc and gVisor), Playwright e2e and compose. They are left to CI. There are no frontend auth changes, so no new frontend tests were added; existing login, logout and session-ended tests are unchanged.

## 14. CI run and skipped jobs

- PR #1 head `e35f6c3`: all 18 jobs succeeded (backend, backend-postgres, web, e2e, compose, sandbox-postgres, sandbox ×6 shards on runc, sandbox-gvisor ×6 shards on runsc), in each of 3 runs. No job was skipped.
- PR #3 head `6ab2754`: all 18 jobs succeeded in each of 2 runs. No job was skipped. The earlier head `3a5c3d4` failed e2e (ambiguous "Research" locator caused by the new account link); fixed in `6ab2754`.

## 15. Research regression

`git diff main` is empty for `diagnosis/`, `adaptation/`, `evidence/`, `learner/`, `content/` and `eval/`. Golden and fixture tests are in the 704-test unit suite, and all passed. Diagnostic v1.3, policy 1.5, the BKT parameters and the thresholds are unchanged.

## 16. Remaining vulnerabilities and risks

1. ~~DB-level case-insensitive uniqueness~~ and ~~password change / login rotation~~: done in PR #3.
2. SQLite's `lower()` folds ASCII only (PostgreSQL follows the locale); lookups and the index use the same function, so they agree per database.
3. **Targeted lockout.** Five failed logins for a known username lock that account for 15 minutes, from any client. Proposal: lock out on (username + client) pairs, plus a higher per-username ceiling that slows logins down instead of blocking them. It is not implemented, because it changes the ADR-029 policy and needs the owner's choice.
4. The per-client throttle is only as good as the proxy configuration (`--forwarded-allow-ips`).
5. gVisor has not been verified on a deployment host. The worker still mounts the Docker socket, which is root-equivalent on the runner VM.
6. The reverse proxy, TLS and the web build's headers are not yet configured anywhere.
7. **D6:** the swallowed adaptation exception remains (future work).
8. There is no `/ready` endpoint (not built; small, recommended for deployment).
9. Demo passwords are public in `compose.demo.yaml`. It is local only and must never be exposed.

## 17. Pull request

https://github.com/rupinderkaur1904/codeadapt/pull/1. It is open and assigned to the owner. GitHub would not request a review from the PR author. **Not merged.**

## 18. Acceptance criteria

| # | Criterion | Status |
| --- | --- | --- |
| 1 | edygvs recovered and preserved | **Blocker: not on GitHub; owner chose GitHub only** |
| 2 | Pushed without rewriting history | Not applicable to edygvs. The new branch was pushed without force. |
| 3 | PR opened against main | Done (#1) |
| 4 | ADR-039 changes reviewed | **Not possible** (ADR-039 is only on edygvs). ADR-040 written instead. |
| 5 | Migration 0006 reviewed and tested | The original 0006 is lost; a **new** 0006 (PR #3) is written and tested up/down/collision on SQLite and PostgreSQL |
| 6 | Password and session security verified | Done, with the gaps listed in 6 and 16 |
| 7 | Role-based authorization verified | Done |
| 8 | IDOR tests on the important endpoints | Done |
| 9 | Production fails closed | Done |
| 10 | Dev role injection rejected in production | Done (ignored, never honoured; tested) |
| 11 | Production requires gVisor | Done in code and in a CI check; not verified on a real host |
| 12 | No runc fallback in production | Done |
| 13 | Host validation and headers | Done for the API; the web build's headers are a proxy task |
| 14 | PostgreSQL tests pass | Done (local 714/714; CI backend-postgres and sandbox-postgres green) |
| 15 | Sandbox regression passes | Done (runc and gVisor, all shards green) |
| 16 | Frontend and e2e pass | Done (45 vitest; Playwright e2e green) |
| 17 | Full CI green | Done on both PRs |
| 18 | Diagnostic v1.3 and policy 1.5 unchanged | Done |
| 19 | No merge into main | Done |

**Milestone 2 is complete except for what the lost branch made impossible:** criteria 1 and 4 (recovering and reviewing edygvs/ADR-039) cannot be met from GitHub. Everything else is done and green; merging is yours.

## 19. Recommended Milestone 3

1. `/ready` (DB + schema revision check) for the deployment's health probe.
2. A throttling policy decision (see 16.3).
3. Deployment-host verification: gVisor sandbox suite on the runner VM, reverse proxy with TLS, Host and headers, and `forwarded-allow-ips`.
4. Fix D6 (adaptation failure).

## Direct answers

- **Was the original auth branch recovered?** No. It is not on GitHub, and it was not used from the laptop at the owner's instruction.
- **What did ADR-039 change?** It cannot be verified from GitHub. The 2026-10-27 report *claims* role permissions, session rotation, password change, case-insensitive usernames (migration 0006), a Host check, headers, a body limit, gVisor enforcement and `/ready`. None of that code is available.
- **Is authentication safe enough for a controlled student pilot?** The code is, once PRs #1 and #3 are merged: fail-closed config, case-insensitive accounts, password change, rotation, tested authorization. A pilot still needs a deployment host with gVisor verified, the reverse proxy configured, a throttling decision, and owner approval for exposure and ethics (M9).
- **Can students escalate privileges?** Not through the API in production, as tested: the dev header is ignored, roles live on the server, and unknown roles are denied. Roles can be changed only by someone holding database or CLI access.
- **Can students access each other's records?** No. They get 404 for other submissions, their lists are filtered to themselves, and research endpoints return 403. This is tested.
- **Can production execute C++ without gVisor?** Not with this PR, unless an operator explicitly sets `CODEADAPT_SANDBOX_ALLOW_RUNC=local-demo-only`, which logs a warning. On `main` today, yes.
- **Are the migrations safe?** 0001–0005 are unchanged. The new 0006 changes no rows, refuses to run (and lists the names) if case collisions exist, and downgrades cleanly; tested on SQLite and PostgreSQL.
- **What risks remain?** See section 16.
- **What must be done before deploying?** Merge PR #1 then PR #3, then the Milestone 3 items (/ready, throttling decision, deployment-host gVisor + reverse proxy), then owner approval for exposure. Never use the demo compose stack for deployment.
