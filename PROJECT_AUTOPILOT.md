# Project autopilot

Persistent progress file for the self-directed loop requested by the owner on 2026-10-24.
Reread it and check it against the repository before each task. Status report:
[docs/status-2026-10-24.md](docs/status-2026-10-24.md).

**Current objective:** bring CodeAdapt to a defensible, demonstrable completion state, with
deliverables 1–12 from the owner's brief, without crossing approval gates.

**Branch:** `claude/project-thread-dyivyy` (owner approved pushing here on 2026-10-24; never
force-push; never push to `ce2sv5`, `zyjfh1` or any other branch).

**Iteration:** 8

## Hard limits (owner rules, override everything below)

- PC1: the gate is closed (withdrawn record). Do not count, pair, confirm, read source code,
  apply A1 or write `record.json`. Never claim supervisor approval.
- Do not change the diagnosis method, skill maps, BKT parameters, ledger, policy, feedback
  wording or frozen protocols without owner approval. Label synthetic results as synthetic.
- No deployment, no real-student data, no publication of derived statistics.

## Completion plan

| Id | Objective | Depends | Files | Acceptance | Status |
| --- | --- | --- | --- | --- | --- |
| A1 | Record PC1 withdrawal, deviations, status truthfully | — | docs/preregistration/pc1/{STATUS,DEVIATIONS}.md, permission/CORRECTIONS.md | Frozen files unchanged; gate closed and pinned by tests | **done** a14fcde |
| A2 | Keep amendment A1 + A1b ready as an inactive proposal on the current branch | owner | project files codeadapt/pc1/a1-proposal/a1-v2.patch | Patch applies cleanly; tests pass in a scratch worktree; nothing activated | **done** (54 PC1 tests pass in scratch; not applied; waits for owner) |
| A3 | Claims audit: no doc states real-student accuracy, learning gains or calibrated mastery | — | README, docs/* | Every accuracy figure labelled synthetic or author-written | **done** (no change needed) |
| B1 | Queue/worker idempotency | — | db/queue.py, worker/pipeline.py | Stale worker cannot overwrite; redelivery does not re-run | **done** d78ee21 (ADR-031) |
| B2 | Review sandbox limits and status classification against ADR-020/023/024/028 | — | execution/* | Each limit and status has a test; gaps fixed or documented | **done** f570b5b (compile output limit and stream-mismatch edge cases pinned; SIGKILL-without-deadline is a runtime error, documented) |
| B3 | API validation and error-handling review | — | api/app.py, schemas.py | Malformed input gets 4xx, not 500; tests | **done** f570b5b (18 malformed requests probed; NUL in source was accepted and would fail on PostgreSQL, now 422) |
| C1 | Full test run, recorded | — | PROJECT_AUTOPILOT.md, docs/status-2026-10-24.md | Commands verified today with counts | **done**: unit 348, sandbox 33 + end-to-end re-run 2/2 on d78ee21, web 21 |
| C2 | One documented command per evaluation to reproduce reported numbers | — | docs/evaluation/*, docs/development.md | Re-run reproduces held-out/calibration tables | **done**: fresh held-out and calibration re-runs identical to the adr030 records |
| D1 | CodeNet PC1 Phase F counts | A2 + owner | — | Only after a truthful, accepted record | **blocked (owner)** |
| E1 | Consolidated, labelled results table across all evaluations | — | docs/evaluation/summary.md | Every number traceable to a report; labels on every row | **done** fca1432 |
| F1 | Architecture document matches the code | — | docs/architecture.md | Known mismatch fixed (queue uses an optimistic conditional UPDATE, not SKIP LOCKED); every component checked | **done** 987cc50 |
| F2 | Research report draft with evidence-supported claims only | E1 | docs/research-report-draft.md | Each claim cites a result; limitations section | **done** (draft) 91cb35a |
| F3 | Limitations and future work list | E1 | docs/limitations.md | Complete, consistent with status report | **done** 91cb35a |
| G1 | Demo workflow with expected results, verified locally | C1 | docs/demo.md | Steps run today; outputs match | **done** (run 2026-10-24, output recorded) |
| G2 | Interview-preparation document | F1, E1 | docs/interview-prep.md | Architecture, algorithms, trade-offs, evaluation, limitations | **done** 91cb35a |

## Log

### Iteration 1 (2026-10-24, read-only audit)

- Verified: withdrawn record 323f3a9 closes the gate at both levels (exit 3). Frozen PC1
  files match the manifest. Amendment A1 is in the project files only and was not applied.
- Gap: `scope.publish_derived_statistics` is never read by `pc1.py` (documented as A1b in
  docs/preregistration/pc1/STATUS.md; needs approval because it changes the frozen script).
- Merged `zyjfh1` into the thread branch locally (no conflicts).
- Tests: unit 334 passed; ruff/format/mypy clean; web lint/typecheck/21 tests/build ok.

### Iteration 2

- a14fcde (A1) and d78ee21 (B1) committed and pushed. Unit tests: 341 passed.
- Sandbox suite (Docker, runc, `CODEADAPT_REQUIRE_SANDBOX=1`, started before d78ee21 was
  imported, so it tested 323f3a9 + zyjfh1 + a14fcde): **33 passed in 1570 s**. The two
  end-to-end files were re-run on d78ee21 (see iteration 4).

### Iteration 3

- 987cc50: status report, this plan, architecture matches the code (F1 done).
- fca1432: docs/evaluation/summary.md (E1 done).
- A3 claims audit: grep over README and docs for accuracy, validation, mastery and
  learning-gain wording found no unsupported claim; no change needed.

### Iteration 4

- 91cb35a: docs/limitations.md (F3), docs/interview-prep.md (G2),
  docs/research-report-draft.md (F2). Pushed.
- G1 demo: `docs/demo/run_demo.py` drafted; verification run pending.

### Iterations 5–6

- End-to-end sandbox tests re-run on d78ee21 (worker change): 2 passed in 667 s.
- f570b5b: B2 and B3 (see the table). Unit tests: 348 passed; mypy and ruff clean; the
  OpenAPI schema is unchanged.
- Demo verified on a live API and worker (docs/demo.md, observed output recorded).

## Blockers needing the owner

1. PC1: approve or decline amendment A1 (+A1b); if approved, read the CodeNet paper's
   datasheet yourself and send the exact licence sentence and date.
2. Hosting/deployment (M8): not needed for the research deliverables.

## Next three tasks

1. Owner decision on A1/A1b (see Blockers).
2. If approved: apply a1-v2.patch, CI, then the owner writes a truthful v2 record.
3. Otherwise idle safely: every remaining workstream needs an owner decision (A1/A1b, hosting,
   failing-case feedback proposal, CE1.2/1.3).

## Resume instruction

`git fetch origin && git checkout claude/project-thread-dyivyy`, reread this file, run
`cd backend && uv sync && uv run pytest tests/unit -q`, then continue with "Next three tasks".

### Iterations 7–8

- 43779b6: README links to all deliverables.
- A1 + A1b rebased as `a1-v2.patch` (project files); applied only in a scratch worktree, where
  54 PC1 tests pass. **Not applied to the branch.**
- Held-out evaluation re-run from scratch: identical to docs/evaluation/adr030-2026-10-23/heldout.md.
- Calibration re-run: identical to the adr030 record. CI green on every pushed commit
  (runs 63–66, including the lost-output probe).
