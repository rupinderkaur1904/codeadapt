# Review resolution: lower-bound design record (2026-10-15)

This responds to the owner's review of [lower-bound.md](lower-bound.md) and its six
requirements. It covers what changed, the tests and measurements behind each change, what
is still limited, and what needs the owner's decision. No problems were added. Decision
record: ADR-019 in [../decisions.md](../decisions.md).

All results below come from the demo bank (`content/demo`) under g++ 14.2.0 on runc.
Every case is synthetic (data class `synthetic`), written by the same author as the error
models. None of these results is evidence about real students' code or about learning.

## Summary

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Ledger counts only explained failures (C5) | Done | Unit tests in `test_adaptation.py`; trajectories re-run |
| 2 | Weak-evidence diagnoses (E2, E5) | Done for E2. E5 reviewed, no change | Qualified hypotheses; calibration cases |
| 3 | Compare the behaviour-group rule (C6) with v1 | Measured. **Needs your decision** | Held-out and calibration reports, both methods |
| 4 | Complexity stays an explicit limitation | Done | Methodology §4, evaluation reports, test purposes |
| 5 | Follow-up: passing is not mastery or transfer | Done | Follow-up relation; wording tests |
| 6 | Declared intent checkable; proposals kept apart (C4) | Done | Validation errors on mismatch; reports regenerate byte-identically |

## 1. Evidence ledger (C5)

**Change.** A failed test now becomes skill evidence only when a supported diagnosis
explains it, and only under the selected model's skill. The entry records the model in
`explained_by`. Failures in `AMBIGUOUS`, `UNMODELLED_BEHAVIOUR`, `INSUFFICIENT_EVIDENCE` and
`UNRELIABLE_EVIDENCE` attempts stay in the stored submission but are not skill evidence.
Passed and excluded tests are attributed through probes as before. The policy version is
now `rule_policy` 1.1 (`backend/src/codeadapt/adaptation/ledger.py`).

**Tests** (`backend/tests/unit/test_adaptation.py`):

* `test_ledger_attributes_explained_failures_only_to_the_models_skill`: a
  `no_progress_update` diagnosis has 9 failing tests that also probe equality, boundaries
  and specification. All 9 now go to `loop_termination` only.
* `test_unexplained_failures_are_not_skill_evidence`: covers the four non-diagnosis
  outcomes. Passing tests are still recorded.
* `test_failures_the_selected_model_does_not_own_are_never_reattributed`.
* `test_policy_ranking_counts_only_explained_failures`: the regression case. Both
  candidate problems used to count 78 ledger entries; they now count 48, because the
  unexplained failures no longer count.

**Trajectories re-run.** All 6 scripted learner trajectories in `test_trajectories.py` produce the
same recommendations and verdicts as before. They are acceptance tests of the policy's
mechanics, not evidence about learners.

**Limitation.** In the demo bank all three problems probe the same four skills, so the
ledger change alters evidence counts but no ranking decision. That will stop being true
once problems probe different skills.

## 2. Weak-evidence diagnoses

**E2 `hi_init_last_index`.** In every problem, the tests that detect E2 form one
behaviour group: lower-bound 3 tests, count-occurrences 5, last-less-than 3. Changes:

* Diagnosis v1.1 records `support_behaviours`. When a supported diagnosis rests on one
  group, it adds `evidence_strength = single_behaviour` and a qualification. Its
  decisions are those of v1.
* E2 carries a `known_limitation` in all three `problem.toml` files.
* A *qualified hypothesis* is a diagnosis that is single-behaviour or whose model has a
  known limitation. For one:
  * the student sees "other mistakes can produce the same pattern; treat the hint as one
    possible cause to check, not as the answer";
  * the recommendation says the pattern "has more than one possible cause";
  * the rationale carries `qualified_hypothesis`.
* The follow-up still targets the skill, never the specific bug.

Tests: `test_support_counts_behaviour_groups_and_qualifies_a_single_one`,
`test_multiple_behaviour_groups_are_not_qualified`, `test_feedback.py` (2 tests),
`test_qualified_or_documented_weak_diagnoses_are_passed_on_as_qualified`, and the
trajectory `test_qualified_diagnosis_and_followup_wording_stay_within_the_evidence`.

**The predicted E2 collision, measured.** Two calibration cases test it:

* `clamp_to_last_index.cpp`: a correct search that returns `n - 1` instead of `n`.
  It returns `-1` on the empty array, so it is **not** confused with E2 and abstains as
  `UNMODELLED_BEHAVIOUR`. The design record said no input separates them; that was wrong
  for this form and has been corrected.
* `clamp_with_empty_guard.cpp`: the same clamp with `if (a.empty()) return 0;`. No input
  separates it from E2, and v1 diagnoses it as E2. This is the false positive the design
  predicted. It is now reported as qualified.

**E5 `stops_at_first_match`.** Its detecting tests form 2 behaviour groups
(`duplicates_middle`; `duplicates_all` with `large_duplicates`), and its predictions are
exact index values. Two calibration cases of a different duplicate error
(`last_of_run.cpp`, `exact_search_walk_back.cpp`) both abstained as unmodelled. A
same-concept variant written in another style (`stop_on_match_upper_mid.cpp`, closed
interval, midpoint rounded up) was diagnosed as E5, which matches its label. No collision
has been found, so E5 is not marked qualified. Its evidence still comes only from inputs
with repeated targets. Proposal C1 (`pair_equal_target`) would add a small-input test.

## 3. Behaviour-group rule (C6) against v1

`v2-candidate` is the same method with `min_behaviours = 2`. A diagnosis needs supporting
tests from at least 2 behaviour groups; otherwise the result is `INSUFFICIENT_EVIDENCE`. It
can be selected with `codeadapt-eval --method`; the worker still runs v1.1. Each case was
run twice, and every case was reproducible under both methods.

**Held-out set** (17 cases: 13 buggy, 4 correct, of which 9 have a modelled bug):

| Metric | v1.1 (deployed) | v2-candidate |
| --- | --- | --- |
| Coverage (buggy cases diagnosed) | 9/13 | 7/13 |
| Correct diagnoses (selective accuracy) | 9/9 | 7/7 |
| False-positive diagnoses | 0 | 0 |
| Modelled bugs not diagnosed | 0/9 | 2/9 |
| Abstentions on buggy cases | 4 (unmodelled 4) | 6 (unmodelled 4, insufficient 2) |
| Correct programs with no failure observed | 4/4 | 4/4 |

The 2 cases v2 loses are both true E2 diagnoses (`recursive_last_index.cpp`,
`bounded_by_last_index.cpp`).

**Calibration set** (5 lower-bound cases written after the design analysis; reported
separately, never pooled):

| Metric | v1.1 | v2-candidate |
| --- | --- | --- |
| Coverage | 2/5 | 1/5 |
| Correct diagnoses | 1/2 | 1/1 |
| False-positive diagnoses | 1 (`clamp_with_empty_guard` as E2) | 0 |
| Abstentions | 3 (unmodelled 3) | 4 (unmodelled 3, insufficient 1) |

**Reading.** On these cases, v2 trades 2 correct held-out diagnoses for 1 avoided
calibration false positive. All three cases are E2. Both sets are tiny and written by
the model author, so this does not support a claim that either rule is more accurate in
general. In every case, the false positive under v1.1 names the right skill: clamping and
E2 are both `search_space_boundaries` errors, and the follow-up targets that skill.

Reports: [heldout-v1](../evaluation/review-2026-10-15/heldout-v1.md),
[heldout-v2-candidate](../evaluation/review-2026-10-15/heldout-v2-candidate.md),
[calibration-v1](../evaluation/review-2026-10-15/calibration-v1.md),
[calibration-v2-candidate](../evaluation/review-2026-10-15/calibration-v2-candidate.md).

## 4. Complexity

Nothing checks O(log n), and nothing claims to. This is now stated:

* in methodology §4 ("Not assessed: complexity");
* in the limitations of every evaluation report;
* in the `purpose` of every large test ("Does not test the O(log n) requirement").

A linear scan passes every suite (lower-bound E10, measured). Any future check needs its
own validated mechanism, for example counted comparisons through an instrumented harness.

## 5. Follow-up evaluation

The test-based criterion is unchanged. Each evaluation now records its **relation** to the
index problem:

* `same_problem`: a retry, whose failing tests the student has already seen;
* `equivalent_practice`: a linked equivalent or the same family;
* `transfer`: a linked transfer problem;
* `other`.

These are kept separate in the data (`criterion_check` 1.1, migration 0003). A met
criterion's reason says it "meets the recorded test criterion; it is not evidence of
mastery". On a transfer link it adds "a single attempt is not evidence of transfer". The
student sees "That is one passing attempt on these tests; it does not show the idea is
fully learned, and later problems will check it in other settings."

The plan for equivalent practice and later transfer problems is unchanged (gaps G1–G3).
The demo bank has no transfer problem yet, so no follow-up can be `transfer` today.

Tests: `test_followup_records_its_relation_and_never_claims_mastery`,
`test_transfer_links_are_reported_as_transfer_but_not_as_demonstrated`, and the trajectory
wording test, which checks that "mastered", "mastery" and "transfer" never reach the
student.

## 6. Declared intent and proposals (C4)

* `problem.toml` now carries:
  * per test: `purpose` and `distinguishes`;
  * per model: `known_limitation`;
  * links: `[curriculum]`.
  The loader rejects unknown models and unknown or self-referencing links.
* Validation errors when a declared `distinguishes` differs from the measurement. It warns
  when a test declares nothing, when a test separates nothing and states no purpose, and
  when a model rests on fewer than 2 behaviour groups without a documented limitation.
* All 45 tests in the bank declare their intent, and every declaration agrees with the
  measurement. The only weak model is E2 in each problem, and it is documented.
* `codeadapt-content report` wrote
  [../content-reports/](../content-reports/). A second run produced byte-identical files.
* The initial `distinguishes` values were written from the measured matrix and reviewed
  against the design record. From now on they act as a lock: any later change to tests or
  models that alters what a test separates fails validation until someone updates the
  declaration on purpose.
* Proposals C1 and C2 are **not** in `content/demo`. Their sources live in
  [proposals/lower-bound/](proposals/lower-bound/), outside the catalogue, with the two
  rejected patterns E9 and E10.

**Regression.** The v1.1 held-out report differs from the M7 report only in the method
version, the new case-set label, the content hashes (the `problem.toml` files gained
declarations) and the added complexity limitation. Every case's outcome is unchanged.

**Full suites.** Backend: 200 passed and 1 failed in the full run (169 unit, 32 sandbox).
The failure was an infrastructure timeout: `docker kill` exceeded 15 s while the host was
heavily loaded, and it aborted one sandbox evaluation test. Re-run alone, that test passed.
Web: 18 unit tests passed; the end-to-end test passed. Details are in
[../development.md](../development.md).

## Decisions for you

1. **C6.** Keep v1.1, where weak E2 diagnoses are reported as qualified, or adopt
   v2-candidate, where they become `INSUFFICIENT_EVIDENCE`. My recommendation is to keep
   v1.1 for now: v2 removed 2 of 2 correct held-out E2 diagnoses to avoid 1 constructed
   false positive, and that false positive already targets the right skill and is worded
   as one possible cause.
2. **C1 and C2.** Apply the two proposed tests and three proposed models to lower-bound.
   This changes its content version.

## Remaining limitations

* The held-out and calibration sets are small (17 and 5 cases) and come from one author.
* Behaviour groups are relative to the modelled programs. A new model can raise or lower
  a diagnosis's strength, which is why content changes are versioned.
* A qualified hypothesis is still a hypothesis from the modelled error space. The
  qualification describes the evidence, not a probability of being right.
* The skill mapping is the author's assumption and has not been validated against expert
  labels or real submissions.
* Under heavy host load, `docker kill` can exceed its 15 s limit. The worker requeues the
  job, but `codeadapt-eval` aborts the whole run instead of recording an infrastructure
  error for that case. This is pre-existing and left for M8.
