# End-to-end validation after the frontend integration (2026-10-25)

**Commits tested.**

- `159162a`: the merge of `claude/project-thread-9vflva` (`1d16d74`), plus the e2e and demo-doc
  changes.
- `abd4b33`: adds documentation only.

**What these results are.** Each result is a technical check of the mechanism: plumbing,
isolation, determinism, and rule application. None of them measures diagnostic accuracy on
real code, learning, or the accuracy of mastery estimates.

## Local runs

The local container has g++ 14.2.0, Docker with `runc`, and image
`codeadapt-sandbox:gcc14.2-1`.

| Check | Command | Result |
| --- | --- | --- |
| Backend unit and integration tests, no sandbox | `cd backend && uv run pytest -q tests/unit` | **373 passed** (32.9 s) |
| Lint, format, types | `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run mypy` | Clean: 101 files formatted, no mypy issues |
| Sandbox: end-to-end, adaptation, execution, security | `uv run pytest -q tests/sandbox/test_end_to_end.py tests/sandbox/test_adaptation_end_to_end.py tests/sandbox/test_execution.py tests/sandbox/test_security.py` | **31 passed** (560 s), none skipped |
| Web | `cd web && npm ci && npm run lint && npm run typecheck && npm run format:check && npm test && npm run build` | All pass. **27 tests** in 6 files. The build gives only the known 650 kB PracticePage chunk warning. |
| Browser, all specs (API + worker + sandbox + UI) | `cd web && npx playwright test` | **3 passed** (2.6 min): login, student practice, researcher |
| Browser, researcher spec after it was extended | `npx playwright test e2e/research.spec.ts` | **1 passed** (1.9 min) |
| Demo compose file | `docker compose -f compose.yaml -f compose.demo.yaml config -q` | Valid |

**What the browser researcher spec covers now:**

1. Landing page, then "Start digging", then `/problems`.
2. A student submits a buggy program and sees the hint, with no internal labels and no P(known).
3. "My attempts" lists the attempt, still with no internal labels.
4. As researcher: Research, then the submission's trace (method, model, adaptation).
5. Learners, then `dev-student`, then the learner model. It shows "estimated under assumed
   parameters" and an `incorrect` observation on `problem_specification`.

**What the sandbox adaptation test covers.** It runs submission → diagnosis → evidence ledger →
LM1 BKT → recommendation:

- a compile error, which gives no observation;
- a named diagnosis, which gives one counted `incorrect` observation on the model's skill;
- an abstention under rule 8a, which gives no negative evidence and, by L19, one `correct`
  observation;
- a retry, which is listed but not counted;
- a correct follow-up, which is counted;
- the display threshold;
- the researcher-only access checks.

## CI on 159162a (run 94)

**All 16 jobs passed** ([run 94](https://github.com/rupinderkaur1904/codeadapt/actions/runs/40171972874), about 24 min):

- backend: lint, format, types, tests, dependency audit;
- backend-postgres;
- web;
- e2e (Playwright);
- compose (build, start, one worker-processed submission);
- sandbox shards core, end-to-end, adaptation and heldout-evaluation;
- sandbox-postgres;
- sandbox-gvisor shards core, end-to-end, adaptation, heldout-evaluation and demo-content;
- the runc `sandbox (demo-content)` shard, covering all 12 problems.

## Not run, or not covered

| Item | Why | Covered elsewhere |
| --- | --- | --- |
| `test_demo_content.py` and `test_evaluation_harness.py` locally | Slow (about 13 min for demo-content); unchanged by this merge | CI shards demo-content and heldout-evaluation, under both runc and gVisor |
| gVisor locally | No `runsc` in this container | CI gVisor shards. CI-tested only; no production claim. |
| PostgreSQL locally | No server here | CI backend-postgres and sandbox-postgres |
| The `compose.demo.yaml` login-mode stack end to end | CI's compose job runs `compose.yaml` only | Config validated locally. The login flow is covered by `e2e/login.spec.ts`, not under compose. |
| Research-page pagination against a real API with more than 100 rows | No e2e fixture | `ResearchPage.test.tsx` (unit). The backend clamps `limit` to 200 and `offset` to at least 0. |
| Real learners, real code | Not authorised; no data | — |
