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
| Held-out, bank expansion (2026-10-24) | Same kind, for the 8 new problems; each problem's cases were committed after its content and before its evaluation | the author's intended bug | 62 cases (46 incorrect, 16 correct), 8 problems |
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
cases reproducible across 2 runs. **Reproduced from scratch on 2026-10-24** (commit 43779b6,
fresh sandbox runs, `uv run codeadapt-eval --content ../content/demo --heldout ../eval/heldout
--compare v1.1 v1.2 v1`): the comparison table is identical to the recorded `heldout.md`. The calibration re-run
(`--cases ../eval/calibration --case-set calibration`) is identical to `calibration.md`.

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

## Bank expansion, 2026-10-24 (synthetic, author-written, per problem)

Sources:

- [ce1.2-2026-10-24](ce1.2-2026-10-24/README.md): integer-sqrt;
- [ce2-2026-10-24](ce2-2026-10-24/README.md): the other seven problems. Despite the folder
  name, these are a binary-search extension, not the planned CE2 stage.

Method v1.3. Columns:

- **modelled named right / wrong / abstained**: incorrect cases whose truth is one of the
  problem's models;
- **unmodelled abstained**: incorrect cases whose truth is unmodelled;
- **false alarms**: correct cases that received a named diagnosis.

| Problem | Cases | Modelled: right / wrong / abstained | Unmodelled abstained | False alarms |
| --- | --- | --- | --- | --- |
| integer-sqrt (G2) | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| upper-bound | 7 | 3 / 0 / 0 | 2 / 2 | 0 / 2 |
| exact-search | 7 | 3 / 0 / 0 | 2 / 2 | 0 / 2 |
| last-occurrence | 8 | 3 / 0 / 1 | 2 / 2 | 0 / 2 |
| min-capacity (G3) | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| rotated-min | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| rotated-search | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| peak-index | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |

**Across all eight problems:**

- v1.1, v1.2 and v1.3 give identical outcomes on every case.
- Every case is reproducible across 2 runs.
- The one abstention (last-occurrence, midpoint rounded up) was predicted in the design record
  before the run.

**How to read this.**

- **Weak evidence by construction.** The author wrote each modelled case to contain exactly one
  modelled error. So naming it is close to circular, as the 2026-10-21 critical review found
  for the original held-out set.
- **Not a sample.** The cases do not sample how real programs fail. In particular, no case
  exercises the time-limit-only models, and v1.3 would not name those.
- **Coverage is not precision.** A 29/30 naming rate here says nothing about coverage on real
  code. The mutation audits measured about 9% named coverage (VAL1-A2, v1.3).

## Bank expansion, 2026-10-25: four new families (synthetic, author-written, per problem)

Source: [expansion-2026-10-25](expansion-2026-10-25/README.md). Method v1.3; same columns as
above. Every problem is non-recommendable and uses the ADR-033 skill keys.

| Problem | Family | Cases | Modelled: right / wrong / abstained | Unmodelled abstained | False alarms |
| --- | --- | --- | --- | --- | --- |
| first-max-index | arrays | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| second-largest, first run (v1) | arrays | 8 | 4 / 0 / 0 | 1 / 2 (1 named wrongly) | 0 / 2 |
| second-largest (v2) | arrays | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| stock-profit | arrays | 7 | 3 / 0 / 0 | 2 / 2 | 0 / 2 |
| longest-run | arrays | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| plus-one | arrays | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| closest-pair-sum | two-pointers | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| container-water | two-pointers | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| dedup-sorted | two-pointers | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| max-window-sum | sliding-window | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| longest-sum-at-most | sliding-window | 7 | 3 / 0 / 0 | 2 / 2 | 0 / 2 |
| distinct-in-windows | sliding-window | 7 | 3 / 0 / 0 | 2 / 2 | 0 / 2 |
| pivot-index | prefix-sums | 8 | 4 / 0 / 0 | 2 / 2 | 0 / 2 |
| range-sum-queries | prefix-sums | 7 | 3 / 0 / 0 | 2 / 2 | 0 / 2 |

- v1.1, v1.2 and v1.3 give identical outcomes on every case.
- The second-largest v2 row follows a test added after the first run exposed a wrong design
  claim; that case is no longer an independent check. The first-run row stays.
- The same caveats as above apply: the cases are author-written and close to circular.

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
| [ce1.4-2026-10-24](ce1.4-2026-10-24/README.md) | observation capacity per skill on the 12-problem bank (8–12 per skill), and BKT sensitivity | technical only |

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
