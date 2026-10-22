# Proposed ADR-030: no named error from uninformative evidence (for owner approval)

**Status: proposed, not implemented.** The owner approved the proposal-and-replay stage on
2026-10-22. Production stays on `fingerprint_consistency` v1.2, ledger policy 1.2, policy v1.4
and LM1, and v1.1 stays selectable. The candidate rule exists only in
`docs/evaluation/adr030-replay-2026-10-22/replay.py`. It goes into production only after the
owner explicitly approves it.

The numbers ADR-028 and ADR-029 are used on another branch (gVisor settings, authentication).

## 1. Context

VAL1-A2 found 11 wrong names among 50 under v1.2. The rule was applied correctly every time:
in all 11, the reliable evidence was identical to the named model's fingerprint. The evidence
itself carried too little information, in two ways.

- **A constant fingerprint (10 cases).** count-occurrences `upper_uses_strict` predicts 0 on
  every test, so any program that prints 0 everywhere matches it. Examples are a loop that
  never runs, a wrong base case, and a stall the optimiser removed. It is the only one of the
  26 error models with a constant fingerprint.
- **Thinned evidence (1 case).** first-true `B_UOI_031` reads `flags[mid + 1]`. The sanitizer
  excluded the 5 out-of-bounds tests, and those were exactly the tests where
  `stops_one_early` differs from the reference. The remaining tests matched that model.

## 2. Decision (proposed)

A supported diagnosis (rule 8) becomes `insufficient_evidence` when either condition holds:

| Rule | Condition | Recorded in the rationale |
| --- | --- | --- |
| **8a** | The selected model's fingerprint is constant: the same signature on every test | `uninformative: ["8a"]`, `consistent_model` |
| **8b** | An excluded observation is on a test where the selected model's fingerprint differs from the reference's | `uninformative: ["8b"]`, `informative_tests_excluded` |

**Consequences:** they follow from the existing `insufficient_evidence` path, with no new
outcome and no policy change:

- the student sees the failing cases with no hint;
- the ledger adds no `incorrect` observation;
- policy 1.4 gives the abstained retry;
- the researcher view keeps the consistent model.

Method version: 1.3. v1.1 and v1.2 stay selectable.

## 3. Replay (case by case, recorded evidence, nothing re-executed)

The full per-case table is `docs/evaluation/adr030-replay-2026-10-22/replay.md`, with the data in
`cases.json`. Before any number was computed, the replay reproduced every recorded run's v1.2 and v1.1
outcome and model (1,066 and 1,366 runs). One program, first-true `C_AOR_018`, differs between
its two recorded executions under every method. It is an unreliable stack-overflow mutant that
no scored count includes; see `DECISION-REPORT.md`.

| Set (incorrect programs) | v1.2 named / right / wrong | Candidate named / right / wrong |
| --- | --- | --- |
| Held-out (26) | 15 / 15 / 0 | 14 / 14 / 0 |
| Calibration (5) | 2 / 1 / 1 | 2 / 1 / 1 (unchanged; the wrong one is qualified) |
| VAL1-A (98) | 10 / 10 / 0 | 10 / 10 / 0 |
| VAL1-A2 (323) | 50 / 39 / 11 | 30 / 30 / 0 |

**What it buys:** all 11 VAL1-A2 wrong names go, and with them 11 `incorrect` observations on
the wrong skill.

**What it costs:** 10 correct names are lost. These are 9 VAL1-A2 mutants and the held-out
case `same_comparison_twice`, all `upper_uses_strict`. Those programs now get the failing cases
without a hint. VAL1-A2 named coverage falls from 15% to 9%.

Rule 8b alone changes one case, which was wrong, and costs nothing. Rule 8a carries the
trade-off.

## 4. Options for the owner

| Option | Effect on the replay sets | Note |
| --- | --- | --- |
| **A. 8a + 8b as above (recommended)** | 0 wrong names; 10 correct names lost | Simplest rule; no hint for "prints 0 everywhere" |
| B. 8b only | 10 wrong names remain (all `upper_uses_strict`) | Leaves the main source in place |
| C. 8b, and 8a made *qualified* instead of insufficient | No `incorrect` skill observations from 8a. The `upper_uses_strict` hint is still shown, with the qualification wording, to all 20 programs: 10 right, 10 wrong | Keeps a hint that is often useful, but the hint is wrong for half of these programs |

**Recommendation: A.** A program printing 0 everywhere still gets the failing cases, which
show it prints 0. A hint that is wrong half the time is worse than no hint.

## 5. If approved: implementation plan

1. Add `uninformative_is_insufficient: bool` to `FingerprintConsistencyV1` and make method 1.3
   the default. Keep `METHODS["v1.2"]` and `METHODS["v1.1"]` selectable.
2. Unit tests for 8a and 8b, for precedence over 4b, and for the qualified and unqualified
   paths. Regression tests showing that v1.2 and v1.1 results are unchanged.
3. Update the methodology docs and the ADR entry, and put the 8a/8b explanation in the research
   view. No student-facing wording changes: the existing failing-cases view is used.
4. Re-run the held-out and calibration sets in the sandbox, and confirm CI is green.

Unknown: whether real programs hit 8a or 8b often. PC1 would show that.
