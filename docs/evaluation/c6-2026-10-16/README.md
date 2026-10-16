# C6 evaluation: behaviour-group support rule against the current policy (2026-10-16)

The owner asked (2026-10-16) for C6 to be evaluated against the deployed diagnosis policy
without replacing it, on the same cases, with raw counts.

* `v1` is the deployed method, `fingerprint_consistency` 1.1: a diagnosis needs at least
  2 supporting tests (single-behaviour diagnoses are reported as qualified).
* `v2-candidate` is C6: the same rules, plus at least 2 distinct behaviour groups.

Both methods diagnose the *same* collected evidence for each case (`codeadapt-eval
--compare v1 v2-candidate`), so differences come from the rule alone, not from re-runs.
The held-out set (`eval/heldout`, unchanged since commit f7f41ee) and the calibration set
(`eval/calibration`, unchanged since d4c218a) were not edited for this comparison, and
they are reported separately, never pooled.

| File | Cases | Content |
| --- | --- | --- |
| [heldout-before-c1c2.md](heldout-before-c1c2.md) | 17 held-out | before C1–C2 (lower-bound `41dd7907bd39`) |
| [heldout-after-c1c2.md](heldout-after-c1c2.md) | 17 held-out | after C1–C2 (lower-bound `871602bc2bba`) |
| [calibration-before-c1c2.md](calibration-before-c1c2.md) | 5 calibration | before C1–C2 |
| [calibration-after-c1c2.md](calibration-after-c1c2.md) | 5 calibration | after C1–C2 |

Before and after C1–C2, the reports are identical case for case.

## Raw counts

| | Held-out v1.1 | Held-out C6 | Calibration v1.1 | Calibration C6 |
| --- | --- | --- | --- | --- |
| Buggy cases | 13 | 13 | 5 | 5 |
| Correct diagnoses | 9 | 7 | 1 | 1 |
| Incorrect diagnoses | 0 | 0 | 1 | 0 |
| False alarms on correct code | 0 | 0 | 0 | 0 |
| Abstentions | 4 | 6 | 3 | 4 |
| Coverage | 9/13 | 7/13 | 2/5 | 1/5 |

Changed cases (all involve E2 `hi_init_last_index`):

* held-out `count-occurrences/bounded_by_last_index.cpp` (truth E2): true diagnosis → abstained;
* held-out `lower-bound/recursive_last_index.cpp` (truth E2): true diagnosis → abstained;
* calibration `lower-bound/clamp_with_empty_guard.cpp` (truth unmodelled clamp): false E2
  diagnosis → abstained.

E5 `stops_at_first_match`: no held-out case has E5 as truth or diagnosis. The one
calibration E5 case is a true diagnosis under both methods, because E5 already rested on 2
behaviour groups (3 after C1).

## Reading

On this content C6 changes exactly one thing: it withholds every E2 diagnosis, right or
wrong. That is the collision documented in lower-bound.md §4.3: E2 rests on one behaviour
group, and an unmodelled clamp produces the same outputs. On these cases it cost two
correct diagnoses and prevented one incorrect one. The cases are synthetic, few, and
written by the models' author, so these counts are not error rates, and they do not show
which policy is better for real students.

## Recommendation: revise C6, retain v1.1 for diagnosis

* **Diagnosis output (student-facing):** retain v1.1. It already reports E2 as a qualified
  hypothesis ("one possible cause, not the answer"). Under C6, a student whose code has
  exactly the E2 error would get no diagnosis at all, and the evidence does not show that
  this is better than a clearly qualified one.
* **Skill evidence (ledger, and later the learner model):** apply C6's rule there. Today a
  qualified E2 diagnosis still adds failure evidence to `search_space_boundaries`
  (`adaptation/ledger.py` counts every `hypothesis_supported` attempt). That is the
  attribution the calibration case shows can be wrong. Excluding single-behaviour-group
  diagnoses from skill evidence keeps the hint and stops an ambiguous pattern from
  updating a skill estimate. This is a change to ledger policy (1.1 → 1.2), so it awaits
  the owner's decision and would be specified in the component interface document.

Neither option is validated on real students.
