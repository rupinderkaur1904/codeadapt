# Evaluation summary (as of 2026-10-24)

One page pointing to every measured result. **None of these numbers is real-student
accuracy, a learning gain or a calibrated mastery estimate.** Every program evaluated so far
was written by the error models' author (held-out, calibration) or generated mechanically
(mutants). No real-student or public-corpus data has been evaluated (PC1 is blocked;
`docs/preregistration/pc1/STATUS.md`).

## Data sets

| Set | What it is | Labels | Size |
| --- | --- | --- | --- |
| Held-out | Programs written by the error-model author, committed before the method was run on them | the author's intended bug | 32 cases (26 incorrect, 6 correct), 4 problems |
| Calibration | Author-written cases used while designing content; never pooled with held-out | the author's intended bug | 5 incorrect |
| VAL1-A | Single-edit mutants of 3 independently structured correct lower-bound programs | behavioural (output-equivalence to a model); earlier report also used Claude's edit labels | 147 mutants, 98 incorrect and failing |
| VAL1-A2 | Same method on count-occurrences, last-less-than, first-true | behavioural | 487 mutants (496 programs), 323 incorrect and failing |

## Diagnostic method over time (incorrect programs: named / right / wrong)

Production is `fingerprint_consistency` 1.3. v1.1 and v1.2 stay selectable, and their records
are unchanged. Source: [adr030-2026-10-23/README.md](adr030-2026-10-23/README.md).

| Set | v1.1 | v1.2 (ADR-027) | **v1.3 (ADR-030, production)** |
| --- | --- | --- | --- |
| Held-out (26 incorrect) | 19 / 19 / 0 | 15 / 15 / 0 | **14 / 14 / 0** |
| Calibration (5) | 2 / 1 / 1 | 2 / 1 / 1 | **2 / 1 / 1** |
| VAL1-A (98, behavioural labels) | 32 / 27 / 5 | 10 / 10 / 0 | **10 / 10 / 0** |
| VAL1-A2 (323, behavioural labels) | 94 / 75 / 19 | 50 / 39 / 11 | **30 / 30 / 0** |

Other held-out facts under every version: 0 false alarms on the 6 correct programs; 32/32
cases reproducible across 2 runs.

**How to read this.**

- Each change removed wrong names by removing names. This costs coverage. Under v1.3, about 9%
  of incorrect mutants get a named error (30/323), and most get `unmodelled_behaviour` or a
  non-termination symptom.
- "0 wrong" on VAL1-A2 is 0 of 30 named. A sample that small leaves a real error rate of
  several percent possible.
- Under VAL1-A's edit labels, v1.1 named the wrong edit in 17 of 32 cases, all through
  time-limit evidence ([val1a-2026-10-21](val1a-2026-10-21/)). ADR-027 was the response.
- The calibration wrong name (`clamp_with_empty_guard` → `hi_init_last_index`) is a known
  collision, kept visible.

## Earlier milestones

| Report | Result | Method |
| --- | --- | --- |
| [synthetic-2026-10-15.md](synthetic-2026-10-15.md) | 17 cases: 9/13 buggy named, 9/9 right, 4/4 correct passed | v1 (pre-1.1) |
| [review-2026-10-15](review-2026-10-15/) | calibration 2/5 named, 1 wrong | v1.1 |
| [c6-2026-10-16](c6-2026-10-16/) | behaviour-group rule compared on the same evidence | v1.1 vs candidate |
| [ce1.0-2026-10-17](ce1.0-2026-10-17/) | 8 new held-out cases, all 8 named correctly | v1.1 |
| [ce1.1-2026-10-18](ce1.1-2026-10-18/) | first-true: 2/3 modelled named, 0 wrong, 1 false negative | v1.1 |
| [adr027-2026-10-21](adr027-2026-10-21/) | v1.1 vs v1.2 case by case | v1.1, v1.2 |
| [val1a2-2026-10-22](val1a2-2026-10-22/) | coverage 15% pooled (v1.2), wrong 11/50 | v1.2 |
| [adr030-replay-2026-10-22](adr030-replay-2026-10-22/) | replay of every recorded run, run-to-run differences | v1.1–v1.3 |

## Infrastructure and learner-model measurements

| Report | What it measures | Result |
| --- | --- | --- |
| [sandbox-timeouts-2026-10-17](sandbox-timeouts-2026-10-17/) | Whether host load turns a normal run into a timeout | Under load, infinite loops still end by CPU limit or wall deadline; the reference never timed out. This motivated `inconclusive` for wall-only stops (ADR-023). |
| [bkt-sensitivity-2026-10-17](bkt-sensitivity-2026-10-17/) | Dependence of LM1 estimates on the **assumed** parameters | e.g. after C,C the estimate ranges 0.518–0.993 across 81 parameter sets; three corrects give 0.98 under the assumed set. A technical check, not validation. |

## What would count as stronger evidence (not available)

- Programs written by people other than the error-model author: VAL1-B protocol, deferred.
- Real rejected submissions with the author's own later fix: PC1, blocked on a truthful
  permission basis.
- Any learning claim needs a study with real learners and an appropriate design. None is
  planned.
