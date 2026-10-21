# Proposed ADR-027: time-limit evidence is a symptom, not a named error (for owner approval)

**Status: proposed, not implemented.** No production code, content, skill map, ledger
policy, BKT parameter or recommendation rule changes until the owner approves this
document. Production stays on `fingerprint_consistency` v1.1, ledger policy 1.2, learner
model LM1 (`bkt-params-assumed-1`) and policy v1.3. Written 2026-10-21 after the VAL1-A
gate (docs/evaluation/val1a-2026-10-21/README.md).

The owner approved the direction on 2026-10-21. Timeout evidence becomes symptom-level
rather than a specific bug diagnosis. This document is the ADR and the implementation plan
they asked for before any change.

## 1. Context: what VAL1-A showed

The lower-bound mutation audit ran 147 single-edit mutants of three correct styles through
the unchanged pipeline. Of the 98 incorrect, failing mutants:

- **32 got a named diagnosis.** 17 of them named a model that does not match the edit
  (strict labels; 11 of 32 on lenient labels).
- **All 17 wrong names are termination models** (`no_progress_update` ×7,
  `closed_loop_hi_mid` ×10), all unqualified. Only 5 of the 22 termination diagnoses
  matched the edit. All 10 non-termination diagnoses matched.
- **The time-limit fingerprint carries almost no information.** The 22 termination
  diagnoses share 4 distinct signature vectors. Every vector holds both correctly and
  wrongly named mutants, so no rule over these observations can separate them.
- **The group count was misleading.** The method counted 6 and 9 "behaviour groups" for
  these diagnoses, which is the strongest evidence category it has, yet 17 of 22 were
  wrong. Behaviour groups are defined relative to the model set (`diagnosis/groups.py`).
  Many tests that a stalling loop fails differ in which *other* models fail them, not in
  anything the program did. A high group count therefore does not establish specificity
  for time-limit evidence.

A program that hits the CPU-time limit tells us one bit per test: it did not finish. Many
different edits stop progress on the same inputs, such as a wrong update, a wrong
comparison, a wrong initialisation or a deleted statement. Matching that bit pattern to one
error model names a cause the evidence cannot distinguish.

These are synthetic mutants labelled by Claude, not human-reviewed, and not real-student
code. The finding is that the method fails on this class of evidence. It is not an
estimate of how often students would see a wrong name.

## 2. Decision (proposed)

### D1. A distinct outcome for observed non-termination

Add the outcome `non_termination_observed` to `diagnosis.models.Outcome`. It is a new
decision rule, **4b**, of the diagnostic method, which becomes `fingerprint_consistency`
**v1.2**.

> **Rule 4b.** Rules 1–4 apply unchanged first. If any *reliable* failing test has the
> signature `time_limit`, the outcome is `non_termination_observed`. No model is
> selected. The rationale records:
> - `timed_out_tests`, the reliable failing tests that hit the CPU limit;
> - `other_failing_tests`;
> - `consistent_models`, the v1.1 candidates, for research only and never shown to
>   students or used by any consumer.

Consequences of the rule:

- **No termination model is named any more.** A model can be a candidate only if it
  predicts every reliable observation. So whenever a time-limit failure is observed, every
  candidate is a model that predicts a time limit. Rule 4b therefore removes every named
  diagnosis that rests on time-limit observations. Models that predict a time limit
  (`no_progress_update` in all four problems, and `closed_loop_hi_mid` in lower-bound and
  first-true) can no longer be selected by the method. They stay in the content, and their
  predictions still shape `consistent_models` and the ambiguity analysis for other
  models.
- **Mixed failures are covered too.** The rule applies even when the program also fails
  other tests with wrong output. The time limit makes any named model rest on
  undistinguishable evidence. The wrong outputs are still shown to the student as failing
  cases (D4).
- **"Non-termination" is the literal observation, not a diagnosis.** The program used its
  whole CPU budget on that input. That is consistent with a loop or recursion that never
  ends, and also with a program that is merely far too slow. The outcome name follows the
  owner's wording. Its definition, the feedback text and the research view all say
  "did not finish within the time limit", not "has an infinite loop". If the owner
  prefers, the key can be `time_limit_observed`. The behaviour is the same.
- **The version change is recorded with each diagnosis.** Method v1.1 stays registered in
  `METHODS` under the name `v1.1` so that every existing result can be reproduced. The
  deployed name `v1` would point to 1.2 only after approval and implementation.

### D2. Precedence relative to other execution evidence

Rule 4b runs **after** rule 3 (unreliable evidence). Each kind of execution evidence is
handled as follows; only the first row is new.

| What happened on a test | How it is classified today (unchanged) | Effect under v1.2 |
| --- | --- | --- |
| CPU-time limit (SIGXCPU, `execution/classify.py`) | `time_limit` signature, reliable program evidence (ADR-023) | Rule 4b: `non_termination_observed` |
| Wall-clock deadline without the CPU limit | Re-run; then `inconclusive`, never evidence (ADR-023) | Unchanged. Counts toward rule 3 or toward the *excluded* fraction, never toward 4b |
| Sanitizer finding, including `stack-overflow` (`evidence/reliability.py`) | Observation excluded, so it is not reliable | Unchanged. Excluded tests never trigger 4b, even when their plain run hit the time limit |
| Repeated run disagrees (non-determinism) | Observation excluded | Unchanged |
| Crash with a signal or non-zero exit and no sanitizer report | `runtime_error` signature, ordinary evidence | Unchanged. It is a distinct signature and is not a time limit. See §6 Q3 |
| Memory or output limit | `memory_limit` / `output_limit` signature, ordinary evidence | Unchanged in this ADR. See §6 Q3 |
| Container did not start, streams mismatched, end-of-output marker missing | `infrastructure_error`, outcome `execution_error` (rule 2) | Unchanged. Rule 2 runs first |
| More than 34% of tests excluded, or every failing test excluded | `unreliable_evidence` (rule 3) | Unchanged. Rule 3 runs first |

VAL1-A has a concrete example of the precedence. `C_AOR_018` hit the time limit on two
tests whose sanitizer build reported `stack-overflow`. Those observations are excluded,
so the replay (§7) leaves it `unmodelled_behaviour` rather than `non_termination_observed`.

One environment caveat is open (ADR-023). The delivery of SIGXCPU under gVisor (`runsc`)
is untested. If it is not delivered there, genuine time limits there become `inconclusive`
and never reach rule 4b. Evidence would be lost, not invented.

### D3. Skill evidence and learner model: no negative observation from timeouts

With ledger policy 1.2 unchanged, the effect follows from existing code with no ledger
change.

- **`explaining_model` returns None for every outcome other than
  `hypothesis_supported`** (`adaptation/ledger.py`). A `non_termination_observed` attempt
  therefore produces **no `incorrect` skill observation**, and no named-error count for
  any skill.
- **Positive evidence is unchanged (ledger rule C).** A skill whose every reliable probing
  test passed still gets a `correct` observation from the same attempt. That is how
  `unmodelled_behaviour` attempts are treated today. Tests that timed out are failed tests,
  so a skill they probe gets no `correct` observation from that attempt.
- **BKT counting follows the LM1 rule the owner confirmed on 2026-10-17.** Execution was
  reliable and feedback was delivered, so the attempt consumes the problem version's
  counted opportunity but adds no failure observation. It is **not** added to
  `learner/bkt.py` `NOT_EVALUATED`. No BKT parameter or code changes.
- **Regression tests prove each of these points** (§5). They do not just assert them.

A consequence the owner should see. `loop_termination` is the skill of the termination
models. After this change it can receive an `incorrect` observation only from a model that
terminates with wrong output (today only first-true `stops_one_early`), but it can still
receive `correct` observations. Its researcher-view estimate will therefore be biased
upward relative to other skills. This change does not fix that, because fixing it would be
a BKT or display change outside this ADR's scope. The research view should state it. A
proposed note is in §6 Q2.

### D4. Student feedback

`api/feedback.py` gets one new branch. To keep the API and web changes small, it reuses
the existing `FeedbackKind.FAILING_CASES`. The alternative, a new kind `DID_NOT_FINISH`,
would need a schema and front-end change. Either way the branch shows no hint, no error
model, no skill and no `consistent_models`.

> Your program did not finish within the time limit on some cases (marked "time limit"
> below). This usually means a loop or a recursive call stops making progress for some
> inputs, or the approach is far too slow. Look at how your search range changes on
> those cases. Other failing cases are listed too.

The per-test verdicts already show `time_limit` (`TestVerdict.TIME_LIMIT`). The message
names a symptom and two possible causes. It does not claim either. This is student-facing
wording, so it is part of what the owner approves here.

Effect on existing feedback: programs that today get a termination model's hint, such as
`no_progress_update` ("lo = mid…"), will get this message instead. That removes a hint
that was wrong in 17 of 22 VAL1-A cases, and also the hint that was right in 5.

### D5. What would justify naming a specific termination error

Each of the following is a condition. None is assumed to hold.

1. **Behaviour-group count is not enough.** VAL1-A showed 6 to 9 groups with 77% wrong
   names. Any future rule that names a termination model must rest on evidence other than
   time-limit fingerprints and group counts over them.
2. **Evidence must show *why* progress stopped, not just that it stopped.** Candidates:
   - **State at the stall.** An instrumented harness reports the search state (`lo`,
     `hi`, `mid`) at the point where an iteration leaves it unchanged. This needs a harness
     and content-format change, and a design that survives different variable names and
     styles, which is hard for arbitrary student code.
   - **Stall-set discrimination.** Tests are designed so that different stalling edits
     stall on *different* input sets. Their separation must be measured on mutants of
     several correct styles, as in VAL1-A, not assumed from the model set.
   - **Source-level evidence.** For example, the update statements of the loop. This is a
     different method class, and it would need its own validation.
3. **Pre-registered validation before any named termination diagnosis returns:**
   - a mutation audit with at least 3 correct styles, analysed separately for termination
     diagnoses;
   - an upper 95% Wilson bound on the wrong-name rate below 20% (VAL1-A T1), on at least
     20 termination diagnoses;
   - human-labelled agreement from VAL1-B or later on termination errors. "Did not finish"
     is easy to agree on; *which* edit caused it is the open question.
4. **Until then, termination models are not named.** That is all this ADR changes. It
   adds no new evidence source.

## 3. What does not change

- No change to content versions, tests, error models or skill maps.
- No change to ledger policy 1.2, LM1 parameters or counting, or the BKT code.
- No change to v1.1 results, stored diagnoses or existing evaluation reports. Old
  diagnoses keep `method_version` 1.1 and are not rewritten.
- No change to other decision rules, `min_support`, `max_excluded_fraction` or the C6
  candidate (`v2-candidate` stays as it is, with 4b added only if the owner asks).

## 4. Consumers a new outcome touches

| Module | Today | Needed under v1.2 |
| --- | --- | --- |
| `diagnosis/models.py` | 8 outcomes | Add `NON_TERMINATION_OBSERVED`. `is_diagnosis` stays false. |
| `diagnosis/fingerprint_v1.py` | rules 1–8 | Rule 4b, version 1.2, `v1.1` kept in `METHODS`. `docs/methodology.md` §4 updated to match. |
| `adaptation/policy_v1.py` | Unknown outcomes fall through to the **no-failure** branch | **Needs a rule; see decision P below.** Without one, a timed-out attempt would be treated like a pass. |
| `adaptation/followup.py` | Compares probe results | No change needed. A follow-up with timed-out probing tests counts as `CRITERION_NOT_MET` on test evidence. Test added. |
| `worker/adapt.py` `_NO_EVIDENCE` | compile, execution | No change. The attempt is evaluated evidence. Test added. |
| `adaptation/ledger.py`, `learner/bkt.py` | — | No code change (D3). Regression tests added. |
| `api/feedback.py` | match on outcome | New branch (D4). |
| `evaluation/metrics.py` | named diagnosis vs abstention | Report `non_termination_observed` as its own column: a symptom flag, never counted as a diagnosis or as a correct one. |
| `web/src/pages/ResearchPage.tsx` | lists outcome strings | Add the string and the "estimated under assumed parameters / loop_termination has no negative evidence source" note (Q2). |
| DB `outcome` column, String(32) | — | `non_termination_observed` is 24 characters, so no migration. |

**Decision P (needs separate approval, because it changes recommendations).** Today a
termination diagnosis leads policy v1.3 to recommend the sibling problem densest in
`loop_termination`. The options for policy **v1.4**:

- **P1 (recommended).** Treat `non_termination_observed` like the abstaining outcomes:
  retry the same problem, with a review flag, no targeted skill and no success criterion.
  This is what an `unmodelled_behaviour` attempt gets today, so it adds no new policy
  logic. It does not infer a skill from a symptom.
- **P2.** Recommend a `loop_termination`-dense sibling. This targets a skill on symptom
  evidence, which is exactly the inference D3 forbids for the learner model, so it is not
  recommended.

If the owner approves the ADR but not P, the implementation stops before merging. A new
outcome with no policy rule would fall into the no-failure branch.

## 5. Implementation plan (after approval only)

1. **Tests first:**
   - rule 4b in each precedence case in §2 D2, including a time limit on an excluded
     test, mixed time limit and wrong output, and every test timed out;
   - no `incorrect` observation and no named-error count from a timed-out attempt;
   - a `correct` observation still emitted for a fully passed skill;
   - BKT counting consumes the opportunity with no observation;
   - the policy P rule;
   - the feedback branch shows no hint or model;
   - v1.1 still reproduces its old outcome on the same input.
2. **Code** as in §4. `docs/methodology.md` §4 rule list and `docs/decisions.md` ADR-027
   updated in the same commit.
3. **CI green.** Production content validation must be unchanged, because it runs
   reference and model programs, not the method.

## 6. Questions for the owner

| Q | Question | Recommendation |
| --- | --- | --- |
| Q1 | Outcome key: `non_termination_observed` (your wording) or `time_limit_observed` (the literal observation)? | Either. The definition and feedback say "did not finish within the time limit" in both cases. |
| Q2 | Should the research view mark `loop_termination` as having no remaining negative evidence source from time limits? | Yes, as a display note only. It needs your approval because it touches the learner-model view. |
| Q3 | `memory_limit` and runtime crashes are also coarse signatures. Audit them the same way before deciding? | Yes. VAL1-A did not show them causing wrong names, but it was not designed to test them. Do it as a separate audit, and do not change them here. |
| P | Policy rule for the new outcome (§4). | P1. |

## 7. Preview on recorded VAL1-A data (not the approved re-run)

`docs/evaluation/adr027-preview-2026-10-21/replay.py` applies rule 4b by hand to the
recorded v1.1 observations. It changes no code. Result: `val1a-replay.json`. Both recorded
runs of every program give the same replayed outcome.

Results on the 98 incorrect, failing mutants:

| | v1.1 (recorded) | v1.2 (replayed) |
| --- | --- | --- |
| Named diagnoses | 32 (33%, CI 24–42%) | **10 (10%, CI 6–18%)** |
| Wrong name, strict labels | 17/32 (53%, CI 36–69%) | **0/10 (CI 0–28%)** |
| Wrong name, lenient labels | 11/32 | 0/10 |
| Correct names | 15 | 10 |
| `non_termination_observed` | — | 30 (22 former termination diagnoses, 8 former `unmodelled`) |
| Unqualified `incorrect` observations for `loop_termination` | 22 (17 resting on a wrong name) | 0 |
| Programs whose outcome changed outside the incorrect-failing set | — | 0 |

The negative result matters as much as the gain:

- **Named coverage falls to 10%, below the pre-registered T2 threshold of 20%.** Under
  v1.2 the method would name an error on about one mutant in ten. The VAL1-A plan says T2
  means the error-model library covers few plausible errors. That conclusion now applies,
  and the earlier 33% was inflated by wrong termination names.
- **Five correct names are lost.** Those mutants now get the symptom message instead of a
  correct hint.
- **0 wrong out of 10 does not show high precision.** The 95% upper bound is 28%, and the
  10 come from styles A and B of one problem.
- **The labels are still Claude's,** not human-reviewed.

The predicted held-out change has not been run. From the v1.1 report, at least four
held-out cases rest on termination models and would become `non_termination_observed`:

- `count-occurrences/two_searches_stalled_left` (`no_progress_update`);
- `last-less-than/while_true_stalls` (`no_progress_update`);
- `lower-bound/size_t_stuck_left` (`no_progress_update`);
- `lower-bound/negated_closed_loop` (`closed_loop_hi_mid`).

Those four were all *correct* names in v1.1. Held-out coverage would fall from 19/26 to at
most 15/26. Any `unmodelled` held-out case that hit a time limit would also move. No
calibration case rests on a termination model. The approved re-run below gives the exact
numbers.

## 8. Re-run and comparison plan (after approval and implementation)

1. **Preserve the v1.1 results first.** The existing reports stay untouched:
   - `docs/evaluation/ce1.1-2026-10-18/` (held-out and calibration);
   - `docs/evaluation/val1a-2026-10-21/`.

   New results go to `docs/evaluation/adr027-2026-MM-DD/`.
2. **Re-run with both methods in the same environment:**
   - held-out (32 cases);
   - calibration;
   - all 150 VAL1-A programs, with `run_audit.py` given a `--method` argument.

   `--method v1.1` must reproduce the recorded v1.1 outcomes case for case. Any difference
   is reported as an execution-reproducibility finding before any method comparison.
3. **Case-by-case comparison table** for every case in every set, with these columns:
   - v1.1 and v1.2 outcome;
   - selected model;
   - qualification (`evidence_strength`, `known_limitation`);
   - `timed_out_tests`;
   - `consistent_models`;
   - the skill observations each version would add (ledger 1.2, as a single attempt);
   - the policy rule and recommended problem (v1.3 vs v1.4 if P is approved);
   - the feedback kind and whether a hint is shown.

   Aggregates are given with denominators and Wilson intervals:
   - named coverage;
   - wrong-name rate (strict and lenient);
   - abstentions by outcome;
   - `non_termination_observed` count by truth label;
   - `incorrect` observations by skill;
   - correct-code false alarms.
4. **Re-evaluate the VAL1-A thresholds T1–T4 under v1.2, stating each one, including T2
   if it triggers.** The comparison is synthetic. It is not real-student accuracy, and the
   report says so.
5. **Stop and report.** CE1.2 and CE1.3 stay paused whatever the numbers show.
