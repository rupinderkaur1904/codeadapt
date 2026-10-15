# Roadmap

Ordered by dependency. Execution security and evidence integrity come first; a thin
end-to-end slice exists by M3 and is widened afterwards. Each milestone ends with tests
run, docs + decision log updated, and a pushed commit. Status is updated in place.

| M | Name | Depends on | Status |
| --- | --- | --- | --- |
| M0 | Repository foundation | — | done |
| M1 | Sandboxed execution core | M0 | done (dev tier, runc) |
| M2 | Content model + first problem with executed fingerprints | M1 | next |
| M3 | Persistence, worker, API — backend vertical slice | M2 | planned |
| M4 | Student workspace (frontend) — full vertical slice | M3 | planned |
| M5 | Evidence reliability: sanitiser + repeat runs | M3 | planned |
| M6 | Adaptation policy v1 + follow-up evaluation | M3, M5 | planned |
| M7 | Researcher console + synthetic evaluation harness | M5, M6 | planned |
| M8 | Auth hardening, production isolation tier, deployment | M4, M7 | planned |
| M9 | Pilot readiness (real-data separation, consent, study protocol) | M8 + owner input | planned |

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

### M4 — Student workspace
* **Objective:** browser workspace: statement, editor, submit, feedback panel with
  observation-based explanations; attempt history.
* **Tests:** Vitest components; Playwright submit→feedback end-to-end.
* **Acceptance:** a new developer can `docker compose up`, open the app, solve/fail the demo
  problem and see feedback.

### M5 — Evidence reliability
* **Objective:** sanitiser build, repeat runs of failing tests, exclusion with reasons;
  `UNRELIABLE_EVIDENCE` outcome; student-facing UB findings.
* **Acceptance:** seeded UB submissions (OOB read, signed overflow, uninitialised read) are
  excluded/flagged rather than diagnosed.

### M6 — Adaptation v1 and follow-up evaluation
* **Objective:** second and third problems in the binary-search/boundaries family; ledger;
  policy v1 (methodology §5); recommendation with rationale and success criterion;
  follow-up evaluation on the next attempt.
* **Acceptance:** scripted learner trajectories (synthetic) produce the expected
  recommendations and follow-up verdicts; every recommendation has a stored rationale.

### M7 — Research console and evaluation harness
* **Objective:** researcher views (trace, filters, metrics) and `codeadapt-eval` that runs the
  held-out synthetic set and emits the methodology §6.1 metrics with counts.
* **Acceptance:** report generated from a clean checkout; numbers reproduced on a second run.

### M8 — Hardening and deployment
* **Objective:** real auth (Argon2id, sessions, CSRF, rate limits), audit log for researcher
  access, gVisor runtime, runner VM separation, backups, structured logging, deployment docs.
* **Gate:** sandbox suite passes under `runsc` on the deployment host; dependency audit
  clean (`pip-audit`, `npm audit`); no public exposure before this gate.

### M9 — Pilot readiness
* **Objective:** data-class separation verified, consent flow, export for analysis, study
  protocol draft. **Requires owner input** (ethics approval, cohort, hosting).
