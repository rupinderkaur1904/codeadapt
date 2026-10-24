# Abstaining, evidence-traceable diagnosis of implementation errors in novice C++ code: a design study with synthetic evaluation

**Draft, 2026-10-24.** Every number is from a report in `docs/evaluation/`, cited inline. No
result in this draft concerns real students, learning or mastery.

## Abstract

We describe CodeAdapt, a practice platform that diagnoses implementation errors in C++
submissions by matching per-test behaviour against executed fingerprints of known buggy
programs (error models), and abstains when the evidence does not single one out. We evaluate
it on four binary-search problems using author-written held-out programs and two mechanical
mutation audits. Two successive rule changes removed every wrong diagnosis observed on these
sets: time limits became a symptom (ADR-027), and uninformative fingerprints are no longer
named (ADR-030). The cost was coverage. Under the current method, 14 of 26 incorrect held-out
programs and 30 of 323 incorrect mutants received a named error, all of them right. The
held-out set is close to circular, and the denominators are small. The main contribution is
therefore the method and an audit trail showing how evidence quality changed what the system
may say. It is not a demonstration of accuracy on real learners.

## 1. Problem

Automated assessment usually reports only pass or fail. Diagnostic feedback that names a likely
error can help, but a wrong diagnosis can mislead. We set out to build a system whose feedback
is never stronger than its evidence, and to measure where that line falls.

## 2. Method

- **Content** (docs/content-format.md): each problem version has a reference solution, tests
  with declared purposes and skill probes, and executable error models.
- **Fingerprints:** the reference and each error model are executed in the same sandbox on
  every test, per content version and environment.
- **Evidence** (methodology §3): per-test signatures, plus a sanitizer build and a repeat of
  failing tests. Wall-clock-only stops (`inconclusive`), infrastructure errors and
  sanitizer findings are excluded as evidence (ADR-016/020/023/024).
- **Decision rules** (methodology §4): the outcomes are named (`hypothesis_supported`,
  possibly qualified), `ambiguous`, `unmodelled_behaviour`, `insufficient_evidence`,
  `non_termination_observed` and `unreliable_evidence`.
- **Downstream:** a skill-evidence ledger, a researcher-only BKT learner model under assumed
  parameters (ADR-025), and a transparent recommendation policy. These are described but not
  evaluated as learning interventions.

## 3. Evaluation design

| Set | Construction | Labels |
| --- | --- | --- |
| Held-out (32 programs, 26 incorrect) | Written by the error-model author, committed before evaluation | intended bug |
| Calibration (5) | Used during content design, reported separately | intended bug |
| VAL1-A (98 incorrect mutants) | Single edits of 3 correct lower-bound programs (frozen plan) | behavioural; edit labels in the original report |
| VAL1-A2 (323 incorrect mutants) | Same for 3 further problems (frozen plan) | behavioural |

Each program was executed twice; reproducibility is reported. Method versions are replayed on
the same recorded evidence (docs/evaluation/adr030-replay-2026-10-22).

## 4. Results

Incorrect programs, shown as named / right / wrong (docs/evaluation/adr030-2026-10-23):

| Set | v1.1 | v1.2 | v1.3 |
| --- | --- | --- | --- |
| Held-out (26) | 19 / 19 / 0 | 15 / 15 / 0 | 14 / 14 / 0 |
| Calibration (5) | 2 / 1 / 1 | 2 / 1 / 1 | 2 / 1 / 1 |
| VAL1-A (98) | 32 / 27 / 5 | 10 / 10 / 0 | 10 / 10 / 0 |
| VAL1-A2 (323) | 94 / 75 / 19 | 50 / 39 / 11 | 30 / 30 / 0 |

- No false alarm occurred on the 6 correct held-out programs, and 32/32 held-out cases were
  reproducible across 2 runs.
- Under VAL1-A's edit labels, v1.1 named the wrong edit in 17 of 32 named cases. All 17 rested
  on time-limit evidence (docs/evaluation/val1a-2026-10-21).
- Under v1.2, 10 of 11 wrong names came from one model whose fingerprint is constant. The
  eleventh rested on evidence thinned by sanitizer exclusions (docs/evaluation/val1a2-2026-10-22).

## 5. Threats to validity

1. **Circularity:** every correctly diagnosed held-out case was input–output identical to its
   error model on 500 random inputs, so held-out precision mostly shows that the author can
   re-express their own mutants.
2. **Synthetic labels:** mutants are mechanical, and their labels are behavioural or AI-assigned.
3. **Small denominators:** "0 wrong of 30" is compatible with an error rate of several percent.
4. **Narrow scope:** one algorithm family, with shared error models across problems.
5. **No real learners:** nothing here measures learning, feedback usefulness or real error
   distributions.

## 6. Discussion

The audit trail shows a consistent pattern. Evidence that carries little information (one bit
per test from a time limit, or a constant output) produced confident but wrong names. Treating
it as a symptom removed those errors. A practical consequence is that a named diagnosis is the
exception (about 9% of incorrect mutants). The failing-test-case view is what most students
would see, which motivates the failing-case-first proposal (docs/proposals/failing-case-feedback-first.md).

## 7. Planned validation (not done)

- **PC1:** real rejected and accepted CodeNet submissions, protocol frozen
  (docs/preregistration/pc1). Blocked until the data-use basis is recorded truthfully.
- **VAL1-B:** human-written incorrect programs, protocol pre-registered
  (docs/preregistration/val1b). Deferred.

## 8. Reproducibility

Commands are in docs/development.md and in each evaluation directory's README. Method versions
are selectable (`METHODS`), and earlier results are never rewritten.
