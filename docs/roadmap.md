# Roadmap

Ordered by dependency. Execution security and evidence integrity come first; a thin
end-to-end slice exists by M3 and is widened afterwards. Each milestone ends with tests
run, docs + decision log updated, and a pushed commit. Status is updated in place.

| M | Name | Depends on | Status |
| --- | --- | --- | --- |
| M0 | Repository foundation | — | done |
| M1 | Sandboxed execution core | M0 | done (dev tier, runc) |
| M2 | Content model + first problem with executed fingerprints | M1 | done |
| M3 | Persistence, worker, API — backend vertical slice | M2 | done |
| M4 | Student workspace (frontend) — full vertical slice | M3 | done |
| M5 | Evidence reliability: sanitiser + repeat runs | M3 | done |
| M6 | Adaptation policy v1 + follow-up evaluation | M3, M5 | done |
| M7 | Researcher console + synthetic evaluation harness | M5, M6 | done |
| M8 | Auth hardening, production isolation tier, deployment | M4, M7 | in progress (2026-10-22): gVisor flags (ADR-028), auth/CSRF/limits/audit (ADR-029), logs, backup, PostgreSQL CI, deployment guide; deploy host open |
| M9 | Pilot readiness (real-data separation, consent, study protocol) | M8 + owner input | planned |
| CE | Content expansion, designed for diagnosis (docs/content-design) | M7 | CE0 done; C1–C2 applied (ADR-022); C6 revision adopted for skill evidence (ADR-023); CE1.0–CE1.1 done |

---

### M0 — Repository foundation
* **Objective:** a fresh clone can install, lint, type-check and test with one command each.
* **Deliverables:** README, docs set, `backend/` package skeleton with uv lockfile, ruff,
  mypy strict, pytest, `.gitignore`, `.env.example`, CI workflow.
* **Acceptance:** `uv sync`, `ruff check`, `ruff format --check`, `mypy`, `pytest` all pass
  locally and in CI.

### M1 — Sandboxed execution core
* **Objective:** compile a C++ source (optionally with a harness) and run it on N inputs,
  each in an isolated, resource-limited container, returning typed results with provenance.
  No web UI; exercised through a CLI (`codeadapt-run`).
* **Modules:** `execution` (`SandboxBackend` protocol, `DockerSandbox`, limits, results,
  environment probe, reaper), `sandbox/` image definition.
* **Security:** everything in security.md §3; adversarial test suite.
* **Tests:** unit tests for result classification; sandbox tests (Docker required) for
  network denial, filesystem read-only, host secrets not visible, fork bomb, memory limit,
  CPU/infinite loop, output flood, compile-time `#include` of host paths, compile timeout,
  test-to-test isolation, concurrent jobs, cleanup of containers and volumes.
* **Acceptance:** all sandbox tests pass on the recorded environment; no leftover
  containers/volumes after the suite; limitations documented.
* **Known limitations:** runc tier only; timing includes start-up.

### M2 — Content model and first diagnostic problem
* **Objective:** problem definition format (YAML + harness + reference + error-model
  mutants + probe/skill tags), loader with validation and content hashing, and a
  `fingerprint` command that executes reference and mutants on every test.
* **First problem:** `lower-bound` (binary search) with ≥ 5 error models and ≥ 12 tests.
* **Tests:** loader validation errors; content validation (mutant compiles, differs from
  reference, deterministic); discrimination report (which model pairs are separable).
* **Acceptance:** `codeadapt-content validate content/demo` passes; fingerprint report shows
  every error model detectable and lists any indistinguishable pairs.
* **Result (2026-10-15):** `lower-bound` has 15 tests and 5 error models. Every model is
  detected by ≥ 3 tests and every model pair is separated by ≥ 5 tests; no warnings.
  Format documented in [content-format.md](content-format.md).

### M3 — Backend vertical slice
* **Objective:** POST a submission → worker executes → evidence stored → diagnosis v1
  (methodology §4) → student-safe feedback over the API.
* **Modules:** `db` (models + Alembic migration), `worker`, `evidence`, `diagnosis`, `api`.
* **Data/API:** tables `submissions`, `jobs`, `environments`, `execution_runs`,
  `test_observations`, `diagnoses`; endpoints `POST/GET /submissions`, `GET /problems`.
  Temporary dev-only auth (fixed dev user, disabled unless `CODEADAPT_ENV=dev`).
* **Tests:** diagnosis unit tests for every outcome in methodology §4; integration test
  per outcome class using real sandbox runs on demo content; projection test proving the
  student response contains no hidden inputs/labels.
* **Acceptance:** each mutant of `lower-bound` submitted through the API yields
  `HYPOTHESIS_SUPPORTED` or a documented `AMBIGUOUS`; reference yields
  `NO_FAILURE_OBSERVED`; a non-compiling source yields `COMPILE_ERROR`; a held-out
  double-bug yields an abstention.
* **Result (2026-10-15):** met. Through the API and worker with the real sandbox, all 5
  error models gave `HYPOTHESIS_SUPPORTED` for the correct model (support ≥ 2), with no
  `AMBIGUOUS` cases. The reference and a differently written correct solution gave
  `NO_FAILURE_OBSERVED`. A held-out, differently written `<=` bug was recognised. A
  double bug gave `UNMODELLED_BEHAVIOUR`. Syntax and signature errors gave `COMPILE_ERROR`.
  These are synthetic checks of the mechanism, not accuracy measurements.

### M4 — Student workspace
* **Objective:** browser workspace: statement, editor, submit, feedback panel with
  observation-based explanations; attempt history.
* **Tests:** Vitest components; Playwright submit→feedback end-to-end.
* **Acceptance:** a new developer can `docker compose up`, open the app, solve/fail the demo
  problem and see feedback.
* **Result (2026-10-15):** the Playwright test passes locally against the real API, worker
  and sandbox. It submits a buggy solution, sees the targeted hint, submits a fix and sees
  15/15 passing. 11 Vitest component tests pass. The compose stack could not be built in
  the development container, because Docker Hub rate limits and blocked registries stopped
  the base images from downloading, so a CI job builds it, starts it and submits through it.

### M5 — Evidence reliability
* **Objective:** sanitiser build, repeat runs of failing tests, exclusion with reasons;
  `UNRELIABLE_EVIDENCE` outcome; student-facing UB findings.
* **Acceptance:** seeded UB submissions (OOB read, signed overflow, uninitialised read) are
  excluded/flagged rather than diagnosed.
* **Result (2026-10-15):** partly met. An out-of-bounds read and a signed overflow are both
  flagged and lead to `UNRELIABLE_EVIDENCE` with student-facing safety findings. The
  overflow case matters because its outputs were all correct, so without the sanitiser it
  would have looked like a clean pass. **An uninitialised read is not reliably detected,**
  because GCC has no MemorySanitizer; this is documented in methodology §3. Content
  validation now rejects reference solutions and error models that have undefined behaviour.

### M6 — Adaptation v1 and follow-up evaluation
* **Objective:** second and third problems in the binary-search/boundaries family; ledger;
  policy v1 (methodology §5); recommendation with rationale and success criterion;
  follow-up evaluation on the next attempt.
* **Acceptance:** scripted learner trajectories (synthetic) produce the expected
  recommendations and follow-up verdicts; every recommendation has a stored rationale.
* **Result (2026-10-15):** met. Two new demo problems (`count-occurrences`,
  `last-less-than`) validate with executed fingerprints, no warnings, and every pair of
  error models separable. Six scripted synthetic trajectories produce exactly the expected
  sequences of recommendations and verdicts, and a sandbox test runs one learner through
  diagnosis, recommendation, a `criterion_not_met` follow-up and a `criterion_met` one.
  Verdicts are named `criterion_met`/`criterion_not_met` rather than "improved" because
  passing a different problem's tests is not, by itself, evidence of learning (ADR-017).

### M7 — Research console and evaluation harness
* **Objective:** researcher views (trace, filters, metrics) and `codeadapt-eval` that runs the
  held-out synthetic set and emits the methodology §6.1 metrics with counts.
* **Acceptance:** report generated from a clean checkout; numbers reproduced on a second run.
* **Result (2026-10-15):** met. `codeadapt-eval` ran all 17 held-out synthetic cases
  twice in each of two invocations from the working tree, and the two JSON reports were
  byte-identical. On this set: coverage 9/13 buggy cases, selective accuracy 9/9,
  0 false-positive diagnoses, 0/9 modelled bugs missed, 4/4 correct programs with no
  failure observed, 4 abstentions (all `unmodelled_behaviour`, all on cases outside the
  model space), 17/17 reproducible. These numbers are from a small, same-author set and
  are an upper bound, not an accuracy claim (methodology §6.1). Researchers get a
  submission list with filters, outcome counts and a per-submission trace page in the web
  app; students see which problems they have passed. Cross-environment reproducibility
  and `POST /research/replay` are deferred.

### CE0 — Content-design method, tooling and review resolution
* **Objective:** the design method and its tooling (docs/content-design/README.md), plus the
  owner's six review requirements on the lower-bound record.
* **Result (2026-10-15):** met. Declared test intent agrees with the measurement for all 45
  tests in the bank, reports regenerate byte-identically, and held-out outcomes are
  unchanged under diagnosis v1.1. The ledger counts only explained failures (policy 1.1),
  single-behaviour diagnoses are reported as qualified, and follow-ups record their
  relation to the index problem. The C6 support rule was measured, not adopted. Details:
  docs/content-design/review-resolution-2026-10-15.md, ADR-019.
* **2026-10-16:** C1–C2 applied to lower-bound after validation (ADR-022). C6 compared
  with v1.1 on unchanged held-out and calibration sets; production policy unchanged,
  recommendation in docs/evaluation/c6-2026-10-16/README.md.

### EV1 — Trustworthy skill evidence (2026-10-17)
* **Objective:** the evidence contracts of docs/component-interfaces.md (ADR-023 D1–D4), so
  every skill observation a learner model could read is reliable, diagnosis-justified,
  per attempt and tied to its content version. No learner model.
* **Result:** met; see ADR-023 status and docs/development.md. CI on d3919b0 then showed
  the lost-output failure (ADR-020) on a fingerprinting run, so the end-of-output marker
  was added in the runner (ADR-024; no content version changes). Open: lost-output root
  cause unknown, marker validated only against a scripted reproduction, gVisor untested.
* **Next:** LM1.

### LM1 — Researcher-only learner model (2026-10-17)
* **Objective:** standard BKT per skill over `skill_observations`, with assumed parameters,
  visible only to researchers (ADR-025; owner decisions L1–L4). No policy or student change.
* **Result:** implemented; tests cover arithmetic, both outcomes, parameter constraints,
  determinism, excluded evidence, retries, version identity, display threshold and the
  unchanged student API. Nothing about real learners is validated.
* **Next:** CE1 (approved 2026-10-17: E1 staged scope, E2 `recommendable` flag, E3 G1–G3).

### CE1 — Binary-search family completion (2026-10-17, in progress)
* **Plan:** docs/proposals/ce1-content-expansion.md. Stages run one at a time and stop at
  each gate for owner review.
* **CE1.0 (done, at gate):** held-out cases for all 8 model instances that had none
  (committed before evaluation), all 8 diagnosed correctly; earlier held-out and
  calibration results identical; design records for count-occurrences and last-less-than.
  Proposed, not applied: C3/C4, a `hi_skips_candidate` boundary model for those two
  problems (2 behaviour groups each, measured in a scratch copy).
  Owner accepted CE1.0 on 2026-10-18; C3/C4 deferred.
* **CE1.1 (done, at gate):** first-true (G1), not recommendable by policy v1.3 (ADR-026).
  - Design record committed before measurement; held-out cases committed before evaluation.
  - Boundary target met: `hi_skips_candidate` (2 groups) and `lo_init_one` (3 groups).
  - Held-out: 2/3 modelled diagnosed, 0 wrong, 1 false negative (`returns_any_true`,
    midpoint-dependent), both unmodelled abstained, both correct passed.
  - Earlier problems' versions, held-out and calibration results, and policy
    recommendations are unchanged.
  - Results: docs/evaluation/ce1.1-2026-10-18.

### M8 — Hardening and deployment
* **Objective:** real auth (Argon2id, sessions, CSRF, rate limits), audit log for researcher
  access, gVisor runtime, runner VM separation, backups, structured logging, deployment docs.
* **Gate:** sandbox suite passes under `runsc` on the deployment host; dependency audit
  clean (`pip-audit`, `npm audit`); no public exposure before this gate.
* **Progress (2026-10-22), no deployment:**
  - gVisor: all sandbox tests pass under `runsc` after ADR-028; since 2026-10-24 CI runs every sandbox shard
    under `runsc`.
  - ADR-029: Argon2id accounts created by `codeadapt-admin`, server-side sessions, CSRF,
    login throttling, a per-user submission limit, an audit log and the web login page.
  - JSON logs with request ids; `codeadapt-admin backup` for SQLite;
    docs/deployment.md with the gate checklist.
  - CI is sharded (about 10 min instead of 46).
  - PostgreSQL 16: psycopg driver, all non-sandbox tests pass on it in CI.
  - Open: production image, runner VM, hosting (owner).

### M9 — Pilot readiness
* **Objective:** data-class separation verified, consent flow, export for analysis, study
  protocol draft. **Requires owner input** (ethics approval, cohort, hosting).
