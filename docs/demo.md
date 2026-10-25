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

Alternatively, `docker compose up --build` starts the same stack plus the web UI on
http://localhost:5173.

## 2. Run the scripted demo

```bash
python3 docs/demo/run_demo.py
```

The script submits four author-written lower-bound programs from `eval/heldout/lower-bound/`.
For each one, it prints what the student sees next to the researcher's view. The whole run took
about 3 minutes here, mostly on the first submission, because the worker measures and caches
the problem's fingerprints first.

**Observed output (2026-10-24, runc, 4 vCPUs):**

| Program | Author's intent | Outcome (researcher) | What the student sees |
| --- | --- | --- | --- |
| `correct_iterative.cpp` | correct | `no_failure_observed` | "passed all 17 tests. Tests can show mistakes but cannot prove a solution correct for every input." |
| `upper_bound_closed.cpp` | `upper_bound_confusion` | `hypothesis_supported`, `upper_bound_confusion` | "behaves as if it has this mistake; check whether it does", plus the hint "Check which side of the boundary elements equal to the target end up on." |
| `double_bug.cpp` | two bugs at once | `unmodelled_behaviour` | the failing cases, with no hint |
| `size_t_stuck_left.cpp` | `no_progress_update` | `non_termination_observed` (no model named, ADR-027) | "did not finish within the time limit on some cases… Look at how your search range changes on those cases." |

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

1. Open http://localhost:5173 and choose Lower bound.
2. Paste a program and submit. The feedback panel and the "Recommended next" card appear.
3. Switch the dev role to researcher, open Research, and open the submission's trace.

The Playwright tests automate both parts in CI: `web/e2e/practice.spec.ts` (student) and `web/e2e/research.spec.ts` (trace and learner model).
