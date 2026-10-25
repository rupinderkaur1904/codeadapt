# CE1.0 evaluation: held-out cases for every model instance (2026-10-17)

**Setup.**
- Method `fingerprint_consistency` v1.1 (production); g++ 14.2.0 under runc; 2 runs per
  case.
- Content versions are unchanged: lower-bound `871602bc2bba`, count-occurrences
  `d1b043c04574`, last-less-than `3d52811ae14b`.

**New cases.**
- 8 held-out cases cover the 8 model instances that had none:
  - lower-bound: `no_progress_update`, `stops_at_first_match`, `hi_skips_candidate`,
    `closed_loop_hi_mid`, `returns_wrong_pointer`;
  - count-occurrences: `no_progress_update`;
  - last-less-than: `hi_init_last_index`, `no_progress_update`.
- They were committed in `8a405c0` before the method was run on them.
- Every model instance (17 of 17) now has at least one held-out case.

**Results** ([heldout.md](heldout.md), [calibration.md](calibration.md)).

| Set | Cases | Diagnosed (correct / wrong) | Abstained | Correct code passed | Reproducible |
| --- | --- | --- | --- | --- | --- |
| New held-out cases | 8 (all modelled bugs) | 8 / 0 | 0 | — | 8/8 |
| Earlier held-out cases | 17 | 9 / 0 of 13 buggy | 4 | 4/4 | 17/17 |
| All held-out | 25 | 17 / 0 of 21 buggy | 4 (all unmodelled) | 4/4 | 25/25 |
| Calibration (reported separately) | 5 | 1 / 1 | 3 | — | 5/5 |

**Regression check.** The 17 earlier held-out cases and the 5 calibration cases were
compared field by field with the EV1 baseline runs, and every one is identical.

**Limits.**
- The new cases were written by the error models' author, in a different code style.
  They are not independent.
- Each was written to embody one modelled error, so a correct diagnosis shows that the
  fingerprints recognise that author's variants. It says nothing about real students.
- Unmodelled-case coverage did not grow in this stage.
