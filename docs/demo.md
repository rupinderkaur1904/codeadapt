# Demo workflow

A 10-minute demonstration of the evidence loop on the development stack. **Never expose this
stack to students:** the worker mounts the Docker socket (docs/security.md).

## 1. Start (Linux with Docker; verified 2026-10-24)

```bash
docker build -t codeadapt-sandbox:gcc14.2-1 sandbox/
cd backend && uv sync
export CODEADAPT_ENV=dev CODEADAPT_DATABASE_URL=sqlite:////tmp/codeadapt-demo.sqlite3
uv run alembic upgrade head
uv run uvicorn codeadapt.api.app:create_app --factory --port 8000 &   # API
uv run codeadapt-worker &                                             # runner
cd ..
```

For the web UI without compose, run `cd web && npm ci && npm run dev` in a third terminal, then
open http://localhost:5173. The Vite server proxies `/api` to port 8000. Alternatively,
`docker compose up --build` starts the same stack plus the web UI.

## 2. Run the scripted demo

```bash
python3 docs/demo/run_demo.py
```

The script submits four author-written lower-bound programs from `eval/heldout/lower-bound/`.
For each one, it prints what the student sees next to the researcher's view. The whole run took
about 3 minutes here, mostly on the first submission, because the worker measures and caches
the problem's fingerprints first.

**Observed output (2026-10-24, runc, 4 vCPUs).** It was re-run on 2026-10-25 after the frontend
integration, with identical outcomes, feedback and recommendation, in 2 min 29 s.

| Program | Author's intent | Outcome (researcher) | What the student sees |
| --- | --- | --- | --- |
| `correct_iterative.cpp` | correct | `no_failure_observed` | "passed all 17 tests. Tests can show mistakes but cannot prove a solution correct for every input." |
| `upper_bound_closed.cpp` | `upper_bound_confusion` | `hypothesis_supported`, `upper_bound_confusion` | "behaves as if it has this mistake; check whether it does", plus the hint "Check which side of the boundary elements equal to the target end up on." |
| `double_bug.cpp` | two bugs at once | `unmodelled_behaviour` | the failing cases, with no hint |
| `size_t_stuck_left.cpp` | `no_progress_update` | `non_termination_observed` (no model named, ADR-027) | "did not finish within the time limit on some cases… Look at how your search range changes on those cases." |

> **Update 2026-10-26 (ADR-037).** `upper_bound_confusion` now carries a `known_limitation`
> (L20 S1 case O1), so `upper_bound_closed.cpp` is still diagnosed as `upper_bound_confusion`
> with the same hint, but the student message is the qualified one ("other mistakes can produce
> the same pattern… one possible cause to check") and the attempt adds no skill observation for
> `equality_handling`. The table above is the 2026-10-24/25 record. The re-run on 2026-10-26
> (2 min 29 s; output in docs/evaluation/l20-original-s1-2026-10-26/demo_run.txt) matched it
> in every other row, and in the final recommendation.

Then `GET /api/v1/me/recommendation` (header `X-Dev-Role: student`) returned a `retry` of Lower
bound ("We could not draw a confident conclusion from your last attempt"), with a follow-up
verdict of `not_comparable`.

## 3. What to point out

1. **Abstention:** two of the three incorrect programs get no named error. That is by design.
2. **Wording:** the student sees "behaves as if", never "you don't understand".
3. **Traceability:** `GET /api/v1/research/submissions/<id>/trace` (header
   `X-Dev-Role: researcher`) shows every observation, the excluded tests, the candidate models
   and the rationale.
4. **Honesty about results:** these programs were written by the error-model author. The
   measured numbers and their limits are in docs/evaluation/summary.md.

## 4. Web UI path (compose stack)

1. Open http://localhost:5173. The landing page links to the problem list at `/problems`;
   choose Lower bound. The list has 25 problems in five families. Eight binary-search problems
   carry an **Unreviewed** label: integer-sqrt, min-capacity, upper-bound, exact-search,
   last-occurrence, rotated-min, rotated-search and peak-index. They work and can be practised,
   but the owner has not yet reviewed them for research use (decision 2026-10-25 07:50). The
   label says nothing about their reference solutions, which pass every test. When presenting,
   describe them as unreviewed.
2. Paste a program and submit. The feedback panel and the "Recommended next" card appear.
   "My attempts" lists the student's own history.
3. Switch the dev role to researcher, open Research, and open the submission's trace.
4. Open Learners and choose a learner to see the researcher-only learner model.

For a login-mode demo (no development stub), use
`docker compose -f compose.yaml -f compose.demo.yaml up --build` and the demo accounts
described in `compose.demo.yaml`. It is for `localhost` only.

The Playwright tests automate both parts in CI: `web/e2e/practice.spec.ts` (student) and `web/e2e/research.spec.ts` (landing page, attempts, trace, Learners list and learner model).

## 5. Login-mode rehearsal (2026-10-25)

`compose.demo.yaml` could not be built in the development container: Docker Hub refused the
`node:22-alpine` pull (HTTP 429). So the same settings were rehearsed without compose:
`CODEADAPT_ENV=production`, SQLite, and the two demo accounts. Commands, from the repository
root:

```
docs/demo/login_mode_start.sh /tmp/codeadapt-login-demo
cd backend && uv run --with httpx python ../docs/demo/login_mode_rehearsal.py
```

Observed output (2026-10-25, runc):

```
1. no session, dev header ignored: 401
   wrong password: 401
2. student me: student | problems: 12
3. buggy submission: completed in 105s; internal label hidden from student: True | P(known) hidden: True
   student blocked from research: 403 403
   no CSRF token ->  403
4. researcher list: [('demo-student', 'hypothesis_supported', 'exact_match_sentinel')]
   trace diagnosis: fingerprint_consistency hypothesis_supported exact_match_sentinel
   learner model: estimated under assumed parameters [('problem_specification', 'insufficient_data', ['incorrect'])]
5. logout: 204 -> me after logout: 401
```

**Notes on the output.**

- **Session cookie.** It carries `Secure`. Browsers accept it on `http://localhost`, but the
  script's HTTP client does not, so the script sends the cookie by hand.
- **Unaccepted problems.** The 12 problems (25 since the 2026-10-25 expansion) include the 8 that
  the owner has not accepted (see docs/reviews/2026-10-25/ce1-status.md). They are labelled
  Unreviewed on `/problems`.
- **The compose packaging itself is untested here.** It needs a run with Docker Hub access.
