# Project autopilot

Persistent progress file for the self-directed loop requested by the owner on 2026-10-24.
Reread it and check it against the repository before each task. Status report:
[docs/status-2026-10-24.md](docs/status-2026-10-24.md).

**Current objective:** bring CodeAdapt to a defensible, demonstrable completion state, with
deliverables 1–12 from the owner's brief, without crossing approval gates.

**Branch:** `claude/project-thread-dyivyy` (owner approved pushing here on 2026-10-24; never
force-push; never push to `ce2sv5`, `zyjfh1` or any other branch).

**Iteration:** 2

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
| A2 | Keep amendment A1 + A1b ready as an inactive proposal on the current branch | owner | /mnt project files a1-proposal | Patch applies cleanly; tests pass in a scratch worktree; nothing activated | todo (proposal exists against 447757a) |
| A3 | Claims audit: no doc states real-student accuracy, learning gains or calibrated mastery | — | README, docs/* | Every accuracy figure labelled synthetic or author-written | todo |
| B1 | Queue/worker idempotency | — | db/queue.py, worker/pipeline.py | Stale worker cannot overwrite; redelivery does not re-run | **done** d78ee21 (ADR-031) |
| B2 | Review sandbox limits and status classification against ADR-020/023/024/028 | — | execution/* | Each limit and status has a test; gaps fixed or documented | todo |
| B3 | API validation and error-handling review | — | api/app.py, schemas.py | Malformed input gets 4xx, not 500; tests | todo |
| C1 | Full test run from a clean checkout, recorded in development.md | — | docs/development.md | Commands verified today with counts | in progress (sandbox suite running) |
| C2 | One documented command per evaluation to reproduce reported numbers | — | docs/evaluation/*, docs/development.md | Re-run reproduces held-out/calibration tables | todo |
| D1 | CodeNet PC1 Phase F counts | A2 + owner | — | Only after a truthful, accepted record | **blocked (owner)** |
| E1 | Consolidated, labelled results table across all evaluations | — | docs/evaluation/summary.md | Every number traceable to a report; labels on every row | todo |
| F1 | Architecture document matches the code | — | docs/architecture.md | Known mismatch fixed (queue uses an optimistic conditional UPDATE, not SKIP LOCKED); every component checked | todo |
| F2 | Research report draft with evidence-supported claims only | E1 | docs/research-report-draft.md | Each claim cites a result; limitations section | todo |
| F3 | Limitations and future work list | E1 | docs/limitations.md | Complete, consistent with status report | todo |
| G1 | Demo workflow with expected results, verified locally | C1 | docs/demo.md | Steps run today; outputs match | todo |
| G2 | Interview-preparation document | F1, E1 | docs/interview-prep.md | Architecture, algorithms, trade-offs, evaluation, limitations | todo |

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
- Sandbox suite: running (result to be recorded here).

## Blockers needing the owner

1. PC1: approve or decline amendment A1 (+A1b); if approved, read the CodeNet paper's
   datasheet yourself and send the exact licence sentence and date.
2. Hosting/deployment (M8): not needed for the research deliverables.

## Next three tasks

1. C1: record the sandbox suite result; re-run the end-to-end sandbox tests on d78ee21.
2. F1: reconcile docs/architecture.md with the code.
3. E1: consolidated, labelled results table.

## Resume instruction

`git fetch origin && git checkout claude/project-thread-dyivyy`, reread this file, run
`cd backend && uv sync && uv run pytest tests/unit -q`, then continue with "Next three tasks".
