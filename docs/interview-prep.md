# CodeAdapt: interview preparation

A guide for explaining the project in a placement interview. Every claim here can be checked
in the repository; the file to point at is given in brackets.

## 1. The 30-second answer

CodeAdapt is a C++ practice platform that does more than say pass or fail. It runs a
submission against diagnostic tests in a sandbox. It compares the program's behaviour with
the measured behaviour of known buggy versions ("error models"), and names a likely bug only
when the evidence singles one out. Otherwise it abstains. It then recommends a follow-up
exercise and uses the next attempt as new evidence. Its design rule is that no feedback may
be stronger than its evidence. Results so far come only from synthetic and author-written
programs, so I can describe precision and coverage on those, not real-student accuracy.

## 2. Architecture (docs/architecture.md)

```
Browser (React + TS) ─HTTPS→ API (FastAPI, no Docker access) ─→ DB (PostgreSQL / SQLite)
                                                                   ↑ jobs
                         Runner worker (separate process) ── Docker sandbox per compile and per test
```

- **Why split the API and the worker?** The Docker socket is root-equivalent, so only the
  worker touches it. That split is the trust boundary; everything else is one Python package
  with import rules.
- **Why a database queue and not Redis?** Jobs are durable evidence anyway, and an
  optimistic conditional `UPDATE` (match on state and attempt count) is safe on both
  SQLite and PostgreSQL. Completion is fenced to the current claim (ADR-031).
- **Pure core:** diagnosis and adaptation are pure functions of stored evidence, so any
  method version can be replayed on archived runs. That is how v1.1, v1.2 and v1.3 were
  compared without re-executing anything (docs/evaluation/adr030-replay-2026-10-22).

## 3. Sandbox (docs/security.md, backend/src/codeadapt/execution)

- One container per compile and one per test, from a toolchain image pinned by digest. No
  network, read-only root, dropped capabilities, `no-new-privileges`, limits on memory, pids,
  open files and output (docs/security.md §4). gVisor (`runsc`) is required before any
  public deployment.
- **CPU time versus wall time.** Only the CPU-time limit (`SIGXCPU`) proves that the program
  itself ran too long, because CPU time is charged to the program. A wall-clock stop without
  it looks the same as a stalled host, so it becomes `inconclusive`, not evidence (ADR-023,
  measured in docs/evaluation/sandbox-timeouts-2026-10-17).
- **Infrastructure versus program failure.** Container start failures, a client/container
  exit mismatch, and a missing end-of-output marker (ADR-024) are infrastructure errors.
  They are re-measured and never counted against the student.

## 4. The diagnostic algorithm (docs/methodology.md §4)

1. Fingerprints are measured, not hand-written: the reference and every error model are run
   in the same sandbox on every test, per content version and environment.
2. Each test result becomes a signature: normalised output, runtime error, time limit, and so on.
3. The decision rules apply in order, and the first match wins. For an incorrect program:
   - unreliable evidence → abstain;
   - a CPU time limit → `non_termination_observed`, a symptom with no named model (ADR-027);
   - no model agrees on every reliable test → `unmodelled_behaviour`;
   - two or more agree → `ambiguous`;
   - one agrees, but it explains fewer than 2 failures, has a constant fingerprint, or its
     distinguishing tests were excluded → `insufficient_evidence` (ADR-030);
   - otherwise → `hypothesis_supported`, worded "your code behaves as if…", never "you
     don't understand…".
4. Behaviour groups: tests that every modelled program passes or fails together count as one
   observation, so 5 tests from one group are not 5 pieces of evidence (ADR-019).

**Trade-off to state clearly:** strict consistency buys precision at the cost of coverage.
Two bugs at once, or noise, give `unmodelled_behaviour`.

## 5. Skill evidence, learner model, recommendations

- **Ledger (ADR-023):** only an unqualified supported diagnosis adds an `incorrect` skill
  observation. Infrastructure errors, inconclusive runs, ambiguity and unmodelled behaviour
  add none. There is one observation per (attempt, skill).
- **LM1 (ADR-025):** Bayesian knowledge tracing with **assumed** parameters. It counts only
  the first reliably evaluated attempt per problem version, is shown only to researchers, is
  labelled "estimated under assumed parameters", and is never used to recommend anything.
- **Policy 1.4:** transparent rules, append-only recommendations, and a success criterion
  checked on the next attempt (`criterion_met` / `not_met` / `not_comparable`, never "mastered").

## 6. Evaluation and what it shows (docs/evaluation/summary.md)

| Set (incorrect programs) | Named / right / wrong under v1.3 |
| --- | --- |
| Held-out (26, author-written) | 14 / 14 / 0 |
| Calibration (5) | 2 / 1 / 1 |
| VAL1-A2 mutants (323, synthetic) | 30 / 30 / 0 |

How I would explain it honestly:

- An independent review found that the early "19/19 held-out" result was near-circular. Each
  correctly diagnosed case was input–output identical to its bug model.
- Mutation audits then showed that time-limit evidence named the wrong edit in 17 of 32 cases
  (VAL1-A). ADR-027 made a time limit a symptom instead of a diagnosis.
- A constant fingerprint caused 10 of the 11 remaining wrong names (VAL1-A2). ADR-030 stopped
  naming errors from uninformative evidence.
- Each fix traded coverage for precision, and every earlier result was kept and reproduced.
- What is missing: independent programs. A public-corpus study (CodeNet) was designed and
  pre-registered, but it is blocked until the data-use basis is settled honestly.

## 7. Engineering practices worth mentioning

- Pre-registration: plans and held-out cases are committed before methods are run;
  deviations are logged (docs/preregistration/pc1/DEVIATIONS.md).
- Versioned methods (`METHODS["v1.1"]`, `["v1.2"]`) keep old results reproducible.
- Typed end to end: mypy strict; OpenAPI-generated TypeScript types; CI with ruff, mypy,
  pytest (unit and sharded sandbox), Vitest and a Playwright end-to-end test.
- Integrity over appearance: a permission record entered in error was withdrawn openly, not
  deleted (docs/preregistration/pc1/permission/CORRECTIONS.md).

## 8. Likely questions

- **Why not train an ML classifier?** There are no labelled real data; a classifier would
  give confident labels without traceable evidence. The deterministic engine is replayable
  and abstains (ADR-021).
- **How do you know a diagnosis is right?** On real students, I don't yet. On author-written
  and synthetic programs, precision is high and coverage is low, with small denominators.
- **What's the hardest bug you fixed?** Distinguishing host stalls from real timeouts
  (CPU versus wall clock), and lost container output, now caught by an end-of-output marker.
- **What would you do next?** Get independent programs (CodeNet or human-written), improve
  the failing-case feedback that most students actually see, and add a second problem family.
