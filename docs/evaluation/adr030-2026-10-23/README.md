# ADR-030 re-run: methods v1.1, v1.2 and v1.3 (2026-10-23)

This is the evaluation after implementing method `fingerprint_consistency` 1.3 (ADR-030, rules 8a
and 8b), which the owner approved on 2026-10-23. All data are synthetic or written by the
error models' author. None of this is real-student accuracy, learning or mastery. Earlier
results are untouched.

## What was run

| Set | How | Result |
| --- | --- | --- |
| Held-out (32 cases) | Re-executed in the sandbox, 2 runs per case. Comparison command: `codeadapt-eval --compare v1.1 v1.2 v1` (`heldout.md`, `heldout.json`) | 32/32 reproducible for every method |
| Calibration (5 cases) | As held-out (`calibration.md`, `calibration.json`) | 5/5 reproducible |
| VAL1-A (150 programs), VAL1-A2 (496 programs), held-out and calibration evidence | Replayed from recorded evidence (`../adr030-replay-2026-10-22/replay.py`) | All 1,366 recorded v1.1 runs and 1,066 v1.2 runs reproduced. The production method 1.3 equals the approved candidate rule on all 1,366 runs |

## Results (incorrect programs; named / right / wrong)

| Set | v1.1 | v1.2 | **v1.3** |
| --- | --- | --- | --- |
| Held-out (26) | 19 / 19 / 0 | 15 / 15 / 0 | **14 / 14 / 0** |
| Calibration (5) | 2 / 1 / 1 | 2 / 1 / 1 | **2 / 1 / 1** |
| VAL1-A (98, behavioural labels) | 32 / 27 / 5 | 10 / 10 / 0 | **10 / 10 / 0** |
| VAL1-A2 (323, behavioural labels) | 94 / 75 / 19 | 50 / 39 / 11 | **30 / 30 / 0** |

**Changes from v1.2 to v1.3:**

- **Held-out:** `count-occurrences/same_comparison_twice.cpp` (truth `upper_uses_strict`) becomes
  `insufficient_evidence`. This is a correct name lost, as predicted by the replay.
- **Calibration:** no change. The one wrong name, `clamp_with_empty_guard` → `hi_init_last_index`,
  is unaffected.
- **VAL1-A2:** 20 changes. Of the 20, 11 wrong names are removed (10 by 8a, 1 by 8b) and 9
  correct `upper_uses_strict` names are lost.

The fresh sandbox re-run reproduces the replay's prediction exactly.

**Consequence to keep in mind.** count-occurrences can no longer name its only equality model:
`upper_uses_strict` prints 0 on every test. Programs with that misconception now get the failing
cases without a hint, and no `incorrect` equality_handling observation.

## Not changed

- Policy 1.4, ledger policy 1.2, feedback wording, BKT and its parameters, skill maps, content.
- `METHODS["v1.2"]` and `METHODS["v1.1"]` reproduce every earlier result.
