# Project autopilot

Persistent progress file for the self-directed loop requested by the owner on 2026-10-24.
Reread it and check it against the repository before each task. Status report:
[docs/status-2026-10-24.md](docs/status-2026-10-24.md).

**Overnight directive (owner, 2026-10-24 18:13):** autonomous loop, with these priorities:

1. end-to-end correctness;
2. bank expansion (6–10 complete binary-search problems);
3. diagnosis tests (no rule changes);
4. evidence and attribution;
5. BKT and recommendation integrity;
6. sandbox reliability;
7. evaluation reproducibility;
8. researcher UI and docs.

Status labels: VERIFIED / PARTIALLY VERIFIED / UNVERIFIED / BLOCKED / PROPOSED.

**Current objective (owner, 2026-10-24 17:04):** finish the full existing scope (sandbox,
diagnosis, evidence, attribution, BKT, recommendations, problem bank, researcher UI,
evaluation), integrated and verified, by Wednesday 2026-10-28. Functional completion by Tuesday
night; Wednesday for regression, demo, report checks. No scope cuts, no unrelated features, no
frozen rule/threshold/parameter changes. Phase E deferred (gate closed).

**Owner direction (2026-10-25 07:06):** integrate `9vflva`; investigate the two skill-mapping
flags; clarify CE1.2/CE1.3/L19 ("I have not explicitly approved an unresolved research decision
merely because I asked you to continue development autonomously"); continue end-to-end
validation; keep rules/evidence/BKT/policy unchanged without an explicit decision; CodeNet gate
closed; continue autonomously on authorised work only. No further problem-bank work until the
owner decides on the 8 new problems.

**Owner decisions (2026-10-25 08:01):** option (b) approved for min-capacity (implemented as
ADR-032, narrowest correction, no code change). L19 option B **not** approved: rule C unchanged;
the 421-program observations describe system behaviour and are not independently validated
skill labels. Then finalise: researcher journey, setup and demo instructions, engineering
defects. Phase E stays blocked.

**Owner directive (2026-10-25 10:09): bank of 25.** Add 13 problems in new families (5 arrays,
3 two-pointer, 3 sliding-window, 2 prefix-sum) through the full lifecycle, in batches; keep
every rule, ADR-032, rule C (L19), L20, BKT parameters and policy unchanged; new problems
non-recommendable; keep the seven completion levels apart; then full regression, demo and
report. Owner 10:21: new skill keys for the new families (ADR-033). Owner 10:37: merge the intro
screen once its CI is green.

**Branch:** `claude/project-thread-dyivyy` (owner approved pushing here on 2026-10-24; never
force-push; never push to `ce2sv5`, `zyjfh1` or any other branch).

**Iteration:** 16

**PC1 status:** Phase E proposed — blocked pending code-level permission and owner approval.

## Hard limits (owner rules, override everything below)

- PC1: gate open at `metadata` only (owner's version 2 record, A1). Phase F done; Phase E
  deferred. Never read or run CodeNet source code, activate A2, send the maintainer enquiry,
  edit `record.json` or commit counts. Never claim supervisor approval.
- Pushing main-project work (never CodeNet data) to this branch: approved again 2026-10-24 17:05.
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
| D1 | CodeNet PC1 Phase F counts | A2 + owner | — | Only after a truthful, accepted record | **done** 2026-10-24 on dc4c0e1 (feasible; counts in owner's project files only) |
| D2 | PC1 Phase E: permission assessment, maintainer enquiry draft, preregistration draft, suitability review | D1 + owner | owner's project files `codeadapt/pc1/phase-e-proposal/` | Drafts only; no code read; nothing activated | **proposed — blocked pending code-level permission and owner approval** |
| E1 | Consolidated, labelled results table across all evaluations | — | docs/evaluation/summary.md | Every number traceable to a report; labels on every row | **done** fca1432 |
| F1 | Architecture document matches the code | — | docs/architecture.md | Known mismatch fixed (queue uses an optimistic conditional UPDATE, not SKIP LOCKED); every component checked | **done** 987cc50 |
| F2 | Research report draft with evidence-supported claims only | E1 | docs/research-report-draft.md | Each claim cites a result; limitations section | **done** (draft) 91cb35a |
| F3 | Limitations and future work list | E1 | docs/limitations.md | Complete, consistent with status report | **done** 91cb35a |
| G1 | Demo workflow with expected results, verified locally | C1 | docs/demo.md | Steps run today; outputs match | **done** (run 2026-10-24, output recorded) |
| G2 | Interview-preparation document | F1, E1 | docs/interview-prep.md | Architecture, algorithms, trade-offs, evaluation, limitations | **done** 91cb35a |
| H1 | Bank expansion: complete binary-search problems (**not accepted by the owner; decision pending, see docs/reviews/2026-10-25/ce1-status.md**) | — | content/demo/*, docs/content-design/*, docs/content-reports/*, eval/heldout/* | Per problem: sandbox validation ok, distinguishes = measured, design record, held-out committed before eval, eval recorded, E2 not recommendable | **VERIFIED** for 8 problems: integer-sqrt, upper-bound, exact-search, last-occurrence, min-capacity, rotated-min, rotated-search, peak-index. CI green (runs 90–92) |
| H2 | Integration tests: infrastructure failure, redelivery, content versions | — | backend/tests/unit/test_pipeline_infrastructure.py, test_content_versions.py | Outage leaves no run, diagnosis, recommendation or learner attempt; redelivery adds no attempt; old version keeps its snapshot | **VERIFIED** (unit suite 373 pass) |
| H3 | CE1.4 family report: observation capacity and BKT sensitivity on the 12-problem bank | H1 | docs/evaluation/ce1.4-2026-10-24/ | Technical measurements only | **VERIFIED** 8dbc328 |
| H4 | Playwright specs no longer race for the single worker | — | web/playwright.config.ts | 3/3 pass locally serially | **VERIFIED**: CI run 92 green on eb05bf9 |
| I1 | Integrate frontend branch `9vflva` (landing page, `/problems`, My attempts, Learners, research pagination, demo compose) | — | web/*, compose.demo.yaml, docs/demo.md | Merge without conflicts; e2e follow new routes; all web checks and Playwright pass | **VERIFIED** 159162a: web 27 tests, Playwright 3/3 locally, CI run 94 |
| I2 | Skill-mapping review (min-capacity, rotated-min) | — | docs/reviews/2026-10-25/skill-mapping-review.md | Evidence for/against unique attribution; no mapping change | **done** abd4b33. min-capacity attribution not unique (exact equivalences); L20 added; decision deferred until real-learner use |
| I3 | L19 options brief with measurement | — | docs/reviews/2026-10-25/l19-policy-options.md, l19_measure.py | Current behaviour, options, consequences, recommendation; no rule change | **done** abd4b33. Recommends option B; **PROPOSED, needs owner approval** |
| I4 | CE1.2/CE1.3/BSX factual account and isolated decision | — | docs/reviews/2026-10-25/ce1-status.md | What was done, what changed, deviations; decision card | **done**; decision card posted 2026-10-25 |
| J1 | ADR-032: min-capacity non-unique attribution gives no `equality_handling` evidence (owner option b) | owner 08:01 | content/demo/min-capacity/problem.toml, tests/unit/test_min_capacity_attribution.py, tests/sandbox/test_{demo_content,adaptation_end_to_end}.py, docs/decisions.md, limitations.md, methodology.md | Diagnosis and trace kept; feedback qualified; no `incorrect` obs, no ledger failure, no BKT update; other mappings and policy unchanged | **VERIFIED** locally: unit 382, sandbox 4/4 (adaptation e2e incl. new test, demo-content, end-to-end), held-out re-run byte-identical. CI run 104 green |
| I5 | End-to-end validation report with exact commands | I1 | docs/reviews/2026-10-25/validation.md | Commands, counts, skipped items | **VERIFIED**: unit 373, sandbox 31 locally, Playwright 3/3, CI run 94 |
| K1 | Bank of 25: 13 problems in four new families (ADR-033 skills) | owner 10:09, 10:21 | content/demo/*, docs/content-design/*, eval/heldout/*, docs/evaluation/expansion-2026-10-25/ | Per problem: design checks incl. alternative causes, sandbox validation ok, design record, held-out committed before eval, eval under v1.1–v1.3, pipeline check; status table with 7 levels | **VERIFIED** locally: 25 problems; 100 held-out cases (synthetic) 0 false alarms, 48/48 named right, 26/26 abstained; bank_check 39/39; unit 452. CI run 112 on ed35cf7: all 16 jobs green |
| K2 | Problem list by family; intro screen merged | owner 10:37 | web/src/pages/ProblemListPage.tsx, LandingPage.tsx; merge of 9vflva 1fb72d5 | Web tests, build, Playwright pass | **VERIFIED**: web 34, Playwright 3/3 locally; CI run 112 green |

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

1. **The 8 new problems (CE1.2, CE1.3, BSX).** Owner (2026-10-25 07:50, 07:52): keep
   **provisionally** in the development bank; **not research-validated**; preserve content,
   evaluation records, limitations and `recommendable = false`; no removal, no expansion
   until the review is complete.
2. **L19 evidence rule: UNRESOLVED.** Option B is **not approved**; rule C unchanged. Focused
   analysis delivered: docs/reviews/2026-10-25/l19-focused-analysis.md (breakdown of 421
   programs, label independence: the 94/28 are the system's own attributions, not scored against
   independent labels; trade-off; tests B would need).
3. **L20 (owner principle, 2026-10-25):** where two causes are observationally
   indistinguishable on the valid input domain, the system must not claim to distinguish them.
   min-capacity: **resolved** by ADR-032 (owner approved option (b) at 08:01). Six provisional
   problems: S1 **applied** 2026-10-26 to the 11 clear-cut models (ADR-036); contestable #3
   and #13 unchanged with a written analysis. Four original problems searched 2026-10-26
   (investigation only): 4 clear-cut twins (O1–O4) **not changed, pending owner decision**.
   rotated-min mapping left as is (documented).
4. PC1 Phase E: deferred (permission basis P, then D1–D12). Gate closed.
5. Hosting/deployment (M8).

## Next three tasks

1. **CI green on the merged head** (bank of 25 + intro screen): every shard, including
   `demo-content` with 25 problems under runc and gVisor. Watch its duration (L16).
2. **Remaining safe engineering, no policy content:** a full `compose.demo.yaml` run once
   Docker Hub access works.
3. **On owner decisions only:** L19 (rule C stays), review of the 8 provisional binary-search
   problems, any recommendable status for the new families (L21, L22). No evidence-rule work.

## Resume instruction

`git fetch origin && git checkout claude/project-thread-dyivyy`, reread this file, run
`cd backend && uv sync && uv run pytest tests/unit -q`, then continue with "Next three tasks".

### Iteration 14 (2026-10-26, owner-approved A–D)

- A: L20 S1 on 11 models (ADR-036); contestable-case analysis
  (docs/reviews/2026-10-26/l20-contestable-cases.md).
- B: D1 P-D1a (ADR-035): `banned_names` in 14 problems, validated against the statement;
  banned-name attempts give no skill observations; records and counts kept; trace shows it.
- C: L22 taxonomy (ADR-034): `index_range`/`update_rule` retired, five new keys, a taxonomy
  module, `positive_only_skills` validation, deprecated keys in the learner-model view.
- D: alternative-cause search of the four original problems (investigation only,
  docs/reviews/2026-10-26/l20-search-original.md); found and rechecked an input-mode gap in
  the 2026-10-25 search script (equivalences unchanged).
- All 25 problems have new content versions (docs/evaluation/l20-d1-l22-2026-10-26/).
- Open for owner review: O1–O4; #3/#13; banned-name counting option; plus-one
  `adds_at_front` → `loop_bounds`; pivot-index probe mapping.

### Iteration 13 (2026-10-25)

- 1d16d74 merge of `9vflva` (clean). 159162a: research.spec starts at the landing page and
  reaches the learner model via Learners; checks My attempts hides internal labels; demo.md
  routes. CI run 94: all 16 jobs green.
- abd4b33: owner-decision reviews (skill mappings, L19, CE1 status), L20 in limitations.
- Local: unit 373, sandbox 31 (560 s), web 27, Playwright 3/3.
- 2dc008a: researcher-page tests (pagination, filter resets offset, empty and error states);
  web 31 tests.
- c3d72cb: dated notes in status, report draft, interview prep.
- 887036b: login-mode rehearsal (production settings, demo accounts) with observed output in
  docs/demo.md §5; compose.demo.yaml itself could not be built locally (Docker Hub 429).
- CI compose job now validates the compose.demo.yaml overlay.
- 12420fa: L19 focused analysis (analysis only); L20 owner principle and provisional status
  recorded.
- c43ba45: docs checked against the integrated app: architecture routes, API paging, test layout,
  `.env.example` completeness, development guide. The scripted demo was re-run with identical
  outcomes (2 min 29 s).

### Iteration 14 (2026-10-25)

- Owner 08:01: option (b) for min-capacity approved; L19 option B not approved.
- ADR-032 implemented through the existing documented-collision route (ADR-019, ADR-023 D2):
  `known_limitation` on `strict_day_limit` and `full_day_overflows`. No change to diagnosis,
  ledger, BKT, policy code, other mappings, thresholds or parameters. New min-capacity content
  version; earlier-version snapshots keep their own attribution (D4, pinned by a test).
- Tests: 9 new unit tests (5 fail without the content change); unit suite 382 passed; ruff,
  format, mypy clean; sandbox `test_adaptation_end_to_end.py`, `test_demo_content.py`,
  `test_end_to_end.py`: 4 passed (1427 s).
- min-capacity held-out re-run on the new version: byte-identical outcomes
  (docs/evaluation/adr032-2026-10-25/). Content report regenerated.
- CI runs 98, 99 (includes the compose-overlay validation step), 100, 101: all green.
- Finalisation re-check on b523b1d: Playwright 3/3 (2.3 min); fresh-clone setup per
  docs/development.md works; web build has no warnings (docs/reviews/2026-10-25/validation.md).

### Iteration 17 (2026-10-25, approved audit actions 1–5)

- Owner 13:27 approved five actions. CI run 113 on 63b0a45 (the audit): all 16 jobs green.
- df1e832 (action 1): L21 wording; golden note re-recorded; unit 455.
- 7b962ef (action 2): Unreviewed label on the 8 provisional problems; web 35.
- Action 3: docs/reviews/2026-10-25/l20-search.md + l20-search/ (26 alternatives, fork-per-call
  driver, exhaustive + random domains). 13 of 29 nameable models have a cross-skill twin;
  safeguards S1–S3 proposed, none applied. L20 row updated.
- Action 4: tests/sandbox/test_family_end_to_end.py (last-less-than, stock-profit,
  dedup-sorted, distinct-in-windows, range-sum-queries: correct, named, unmodelled, and
  qualified where available). 5 passed locally in 4 min 54 s (runc). New CI shard
  `families` (runc and gVisor), parallel to the others, so wall-clock CI time should stay set
  by demo-content (~28 min); adds about 2 × 5–8 runner-minutes per push.
- Action 5: docs/proposals/d1-technique-evidence.md and l22-skill-taxonomy.md (documents
  only). L23 added to limitations.

### Iteration 16 (2026-10-25, audit of the bank of 25)

- Owner 12:41: audit only (no bank growth, no policy/mapping/rule change). Verified ed35cf7 =
  remote, CI run 112 all 16 jobs green, local unit 452 / web 34 / Playwright 3/3.
- docs/reviews/2026-10-25/expansion-audit.md: 9-column status matrix for 25 problems; L21
  traced (policy note and student message both false whenever a non-recommendable problem is
  unpassed, also in binary search; wording fix possible without policy change, needs
  approval); L22 mapping table and confounds (pivot-index `index_range` has no model); review
  of the 8 provisional problems (references agree with brute force on 4,800 inputs; linear
  scan and banned calls pass 6 problems and earn rule C evidence = D1; int overflow gives
  `unreliable_evidence`). Pipeline check 27/27 for first-true + the 8.
- L21 row corrected to its full extent; STATUS.md and status doc record CI run 112.
- Discrepancy: the demo does not label the 8 provisional problems "unreviewed" (owner 07:50);
  not changed (user-facing), listed as action 2.

### Iteration 15 (2026-10-25, bank of 25)

- Batches: A1 first-max-index, second-largest, stock-profit, longest-run (b09d42f, held-out
  99c1bb3); A2 plus-one, closest-pair-sum, container-water, dedup-sorted (dc3f07c, a9925ae);
  second-largest v2 (658426c); A3–A4 max-window-sum, longest-sum-at-most, distinct-in-windows,
  pivot-index, range-sum-queries (3b079a2, held-out 778fbbf); evaluations e852b17.
- Design tool `docs/content-design/expansion-2026-10-25/native_matrix.py`: oracle, collisions,
  alternative-cause programs on the tests and on 400 random inputs. Three cross-skill
  equivalences documented via the ADR-032 route; models that collided were dropped
  (min_from_zero, never_removes, squares-sorted problem); shrinking with `if` in
  longest-sum-at-most turned out correct and is not a model.
- Held-out finding: second-largest named an unmodelled case wrongly; the design record's claim
  was wrong; a test was added (v2), first-run record kept, case no longer independent.
- fb95e16: STATUS.md (7 levels × 25), bank_check.py (39/39), unit tests for the non-unique
  models (fail without the `known_limitation`), L20 updated, L22, report §4.1, summary.
- cc58377: problem list grouped by family; landing footnote names the five families.
- 63bfb99: merge of the intro screen (9vflva 1fb72d5, its CI run 110 green); one CSS conflict
  resolved by keeping both blocks. Web 34 tests, build ok; Playwright 3/3 locally (2.5 min) on the merged tree.
- Sandbox daemon had stopped once mid-session (evaluations failed with "docker daemon
  unavailable"); restarted and re-ran; no result came from the failed run.

### Iterations 7–8

- 43779b6: README links to all deliverables.
- A1 + A1b rebased as `a1-v2.patch` (project files); applied only in a scratch worktree, where
  54 PC1 tests pass. **Not applied to the branch.**
- Held-out evaluation re-run from scratch: identical to docs/evaluation/adr030-2026-10-23/heldout.md.
- Calibration re-run: identical to the adr030 record. CI green on every pushed commit
  (runs 63–66, including the lost-output probe).

### Iteration 9

- A1 + A1b applied (63e3773, b11e60d); the owner committed a truthful version 2 record (dc4c0e1).
  CI green on all three (runs 69–71).
- PC1 Phase F run with the frozen script: identification identical, confirm by owner,
  feasibility exit 0, band feasible. Counts kept out of the repository (not publishable).

### Iteration 10 (local commit; owner said not to push)

- Phase E prepared, not approved. Permission assessment: no first-hand evidence covers the full
  archive's source code (IBM's own download page `readme.html` has no licence statement; the
  CODAIT statement covers samples only; AIZU rights unknown). Enquiry drafted, not sent.
  Preregistration draft 0.1 and suitability review written to project files.
- Code gate re-checked: `pc1.py gate --level code` exit 3. No code extracted or read.

### Iteration 11 (owner's completion directive)

- Audit: unit 368 → 370 pass; ruff/mypy clean; web 21 + Playwright 3 pass; CI green on fc4d427.
- 91b41f0: adaptation end-to-end test extended through the LM1 learner model (compile error,
  named, abstained, retry, follow-up); passes in the sandbox (207 s). Pinned limitation L19.
- 91b41f0: worker lease heartbeat (`queue.renew`, fenced); heartbeat test fails without it.
- fc4d427: Playwright test for researcher trace + learner model (3/3 pass locally).
- f583d98: CI job running both end-to-end tests on PostgreSQL 16 (passed locally, 446 s);
  gVisor job now runs every sandbox shard.

### Iteration 12 (overnight directive)

**Bank expansion.**

- 8 new binary-search problems:
  - integer-sqrt (G2);
  - upper-bound;
  - exact-search;
  - last-occurrence;
  - min-capacity (G3);
  - rotated-min;
  - rotated-search;
  - peak-index.
- Each has:
  - a design record;
  - sandbox validation `ok` with measured `distinguishes`;
  - a content report;
  - 7–8 held-out cases, committed before evaluation;
  - an evaluation under v1.1, v1.2 and v1.3.
- **Results.** These are synthetic, author-written cases and are kept separate per problem
  (`docs/evaluation/ce1.2-2026-10-24/`, `docs/evaluation/ce2-2026-10-24/`):
  - every named diagnosis was correct;
  - one predicted safe abstention (last-occurrence, upper midpoint);
  - 0 false alarms;
  - all cases reproducible;
  - no method differences.
- **Recommendations.** All new problems are `recommendable = false`. Policy 1.4 and its golden
  test are unchanged.
- **Single-group models.** These are documented as `known_limitation`:
  - last-occurrence `missing_equality_check`;
  - rotated-min `hi_skips_candidate`;
  - rotated-search `left_half_test_strict`.

**CI failure since run 83.** It was caught late.

- `test_demo_content` asserted exactly one weak model (`hi_init_last_index`) per problem.
- It now requires the weak set to equal the documented `known_limitation` set: stricter for new
  problems, unchanged for the original four. It passed locally in 780 s.

**New tests.**

- Sandbox outage → requeue → failed after 3 attempts, with no run, diagnosis, recommendation or
  learner attempt.
- Redelivery adds no second learner attempt.
- Content-version change keeps the old snapshot through the database.
- Unit total: 373.

**Label slip.** Commits and content comments call the new problems "CE2". The docs now say
these are a binary-search extension (BSX), not the planned CE2 stage (arrays). Content and
held-out files were not edited, because editing them would change content versions and
manifests.

**Iteration 12, continued.**

- CE1.4 report written (8dbc328).
- Evaluation summary table for the bank expansion added (f88e9b8).
- Playwright `research.spec` timed out in CI run 89. It was waiting behind other specs' jobs on
  the single worker. The specs now run serially (`workers: 1`) and pass 3/3 locally.
