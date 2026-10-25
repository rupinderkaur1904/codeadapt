# L19: positive evidence from failing, un-named attempts (2026-10-25)

**Status.** This is a decision brief for the owner. **No rule, threshold or policy was changed.**
The evidence rules (ADR-019 C5, ADR-023 D2 and rule C) are still in force. Its current behaviour is pinned in
`backend/tests/sandbox/test_adaptation_end_to_end.py`.

## Current behaviour

`skill_observations()` in `backend/src/codeadapt/adaptation/ledger.py` gives at most one
observation per attempt and skill:

- **`incorrect`** goes to the skill of the model, when the diagnosis names a model
  unqualified.
- **`correct` (rule C)** goes to every other skill that has at least one probing test, provided
  every one of its probing tests passed and none was excluded. **This applies whatever the
  diagnosis outcome was:** named, qualified, unmodelled, ambiguous, insufficient, or
  non-termination.
- **Nothing** comes from compile errors, execution errors or unreliable evidence.

So a program that fails most tests, and is abstained on, still earns `correct` on any skill
whose tests it happens to pass.

The pinned example is a count-occurrences program that prints 0 for every input.

- It is abstained on (rule 8a).
- It still earns `problem_specification = correct` from the absent-target tests. For an absent
  target, 0 is the right answer.

**Tension with the LM1 text.** `docs/methodology.md` (LM1 counting) says an abstaining first
attempt "yields no observation for the skill". Rule C gives it observations on *other* skills.
These two statements can be read as consistent only if "the skill" means the skill of the
consistent model. The owner's 2026-10-17 confirmation may have meant either reading.

## Measured size of the effect (synthetic)

These figures come from the committed ADR-030 replay, using method v1.3, the current evidence rules and
the production pipeline. The corpus is the 421 VAL1-A and VAL1-A2 mutants labelled
`incorrect_failing`, on lower-bound, count-occurrences, last-less-than and first-true. The replay's `candidate` runs equal production v1.3 on all 1,366 runs (docs/evaluation/adr030-2026-10-23). They are
single-edit synthetic mutants, so this describes the corpus, not real code.

| | lower-bound | count-occurrences | last-less-than | first-true | All |
| --- | --- | --- | --- | --- | --- |
| Incorrect programs | 98 | 108 | 111 | 104 | 421 |
| Named, unqualified | 8 | 0 | 13 | 7 | 28 |
| Not named, with at least 1 `correct` observation | 11 | 49 | 17 | 3 | **80** |
| `correct` observations from not-named programs | 11 | 52 | 23 | 3 | **89** |
| `correct` observations from named programs | 3 | 0 | 0 | 2 | 5 |
| `incorrect` observations | 8 | 0 | 13 | 7 | **28** |

**Reading.** On this corpus, wrong programs produce more than three times as many `correct`
observations (94) as `incorrect` ones (28).

- Of the 89 positives from programs that were not named, 57 are on `problem_specification`.
  Many of these come from absent-target tests, which a constant or near-constant program passes
  trivially.
- This adds to the known optimism of the assumed BKT parameters: see the CE1.4 sensitivity
  report and the critical review.

**Reproduce:** `python3 docs/reviews/2026-10-25/l19_measure.py` from the repository root.

## Options

| Option | Rule | What it fixes | What it costs |
| --- | --- | --- | --- |
| **A. Keep rule C** (current) | As now | Nothing | All 89 positives from not-named programs stay. Estimates stay optimistic, mostly on `problem_specification`. |
| **B. No observations from failing, not-named attempts** | An attempt that failed at least one reliable test and was not named unqualified gives no observations at all, positive or negative. Named attempts keep rule C for their other skills. Passing attempts are unchanged. | Removes all 89 positives above. Abstention then means "no evidence" in both directions, which mirrors the existing rule that their failures are not evidence. The LM1 text becomes literally true. | Fewer observations, on a bank where observation capacity is already thin (CE1.4). Partially correct programs lose credit that may be genuine. |
| **C. Positives only from fully passing attempts** | B, and in addition a named attempt gives only its `incorrect` observation | Also removes the 5 positives from named programs | Smaller gain than B, and more lost capacity. Hard to justify: a named program's other skills were exercised and passed. |
| **D. A pass-rate threshold** | Rule C applies only if the attempt passes at least X% of tests | Removes the worst cases | Adds a new tunable threshold with no empirical basis. Choosing X after seeing these numbers would be fitting the rule to the corpus. |

## Recommendation: B

- B is the smallest rule that removes the measured problem.
- It adds no threshold.
- It treats abstention symmetrically.
- It matches the plain reading of the LM1 text.

**How it would be done, if approved.** It would be a new, selectable version of the evidence rules, like the method versions. The old policy stays selectable, and existing records are
preserved. The work would include:

- regression tests;
- a case-by-case replay over held-out, calibration, VAL1-A and VAL1-A2, reporting the
  observation counts lost;
- a rerun of the CE1.4 capacity and sensitivity report.

The pinned L19 assertion in the end-to-end test would then change, from
`problem_specification` to no observations, with the change documented. The test itself would
not be deleted.

**This is an evidence-policy change, so it needs the owner's explicit approval.** Until then,
rule C stays as it is.

**What this does not establish.**

- Whether real students' failing programs show the same ratio.
- Whether any option makes BKT estimates more accurate. Without real data, there is no accuracy
  to measure.
