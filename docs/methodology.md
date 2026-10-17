# Diagnostic and adaptive-learning methodology

This document defines *what CodeAdapt is allowed to conclude* from execution evidence,
how it decides, and how those decisions are evaluated. It is written so that a reviewer
can check every rule against the code (`diagnosis/`, `adaptation/`) and its tests.

## 1. Principles

1. **Behaviour is not cognition.** An observation supports a hypothesis about an
   *implementation error*. Mapping that error to a *skill* is a modelling assumption,
   stated per error model, and student-facing text says "your code behaves as if…",
   never "you don't understand…".
2. **Passing is not correctness.** All-pass yields `NO_FAILURE_OBSERVED` on the tested
   cases, with the suite's coverage stated.
3. **Abstention is a first-class result.** The method returns no diagnosis whenever the
   evidence doesn't discriminate, doesn't fit the model, or is unreliable.
4. **No fabricated numbers.** v1 reports *counts* (supporting tests, contradicting tests)
   rather than probabilities. A calibrated probability is only reported once a method is
   calibrated on data with ground truth, and the calibration data is cited.
5. **Replayable.** Diagnosis and adaptation are pure functions of stored evidence plus
   content version, so any method version can be re-run over archived evidence.

## 2. Content model for a problem

For each problem version:

* **Interface.** Typically a function signature (e.g. `int lower_bound_index(const std::vector<int>& a, int x)`)
  linked with a **private harness** that reads one test input, calls the function and
  prints the result. Plain stdin/stdout problems are also supported.
* **Reference solution** (private).
* **Diagnostic tests.** Each test has a key, input, `visibility` (`sample`/`hidden`), and
  **probes**: named properties it exercises (e.g. `empty_input`, `target_above_all`,
  `duplicates_run`, `large_index`). Probes map to **skills** (e.g. `loop_boundaries`,
  `empty_case_handling`, `integer_overflow`).
* **Error models.** Each is a known-buggy *executable* implementation (a mutant) plus
  description, implicated skill, and a student-safe hint. Examples for lower-bound:
  `upper_bound_confusion` (uses `<=`), `off_by_one_hi` (`hi = n-1` initialisation),
  `no_progress_loop` (`lo = mid` → non-termination), `midpoint_overflow`
  (`(lo+hi)/2` on large indices), `empty_unhandled`.
* **Fingerprints.** The behaviour of each error model and the reference on each test,
  obtained **by executing them in the same sandbox and environment**. Predictions are
  therefore measured, reproducible and tied to an `environment` record — not hand-written.

A content-validation step (CI) rejects a problem version where a mutant fails to compile,
behaves identically to the reference on every test (the suite cannot detect it), or
behaves non-deterministically across repeated runs.

## 3. Evidence normalisation

Each test run becomes an **observation** with an *outcome signature*:

| Signature | Meaning |
| --- | --- |
| `output:<normalised stdout>` | exited 0; stdout after whitespace normalisation |
| `runtime_error:<signal or exit code>` | non-zero exit or signal |
| `time_limit` | stopped by its CPU-time limit (the program itself used the CPU; ADR-023) |
| `memory_limit` | killed by the memory cgroup |
| `output_limit` | exceeded output cap |
| `inconclusive` | stopped by the wall clock without reaching its CPU limit, also after one re-run with a 10 s start-up grace; a host stall looks the same, so not evidence (ADR-023) |
| `infrastructure_error` | sandbox failure — not evidence about the program; student runs re-measure it up to 3 times |

**Reliability marking.** A test observation is excluded (and listed as excluded, with the
reason) when:

* the sanitiser build (`-fsanitize=address,undefined`) reports a finding on that test →
  undefined behaviour, output not trustworthy;
* a repeated run of the test produces a different signature → non-determinism;
* the observation is an `infrastructure_error`.

UB found by the sanitiser is itself reported to the student as an actionable finding
("reads or writes outside the bounds of an array or vector", with the cases where it
occurred), separately from the diagnosis.

**As implemented (M5).** Every test runs once in the standard build. Every test whose
signature differs from the reference is run once more. If the second run disagrees, the
test is excluded as non-deterministic. The ASan + UBSan build runs every test, and any test
whose sanitiser report names a finding is excluded. Leak reports are ignored, and so are
time-limit results that appear only under the slower sanitiser build. Content validation
applies the same sanitiser build to the reference and every error model, and rejects
content whose predictions rely on undefined behaviour.

**Known blind spot.** GCC has no MemorySanitizer, so **reads of uninitialised variables
are not detected directly**. Such reads are caught only when they make repeated runs
disagree, which is not guaranteed. A clang/MSan build profile is the planned remedy, and it
needs an MSan-instrumented standard library.

## 4. Diagnostic method v1: fingerprint consistency with abstention

Inputs: reliable observations *O*, reference fingerprint *R*, error-model fingerprints
*{M₁…Mₖ}*. For a test *t*, `agree(X, t)` ⇔ the observed signature equals *X*'s signature.

Decision procedure (evaluated in order; first match wins):

| # | Condition | Outcome |
| --- | --- | --- |
| 1 | compilation failed | `COMPILE_ERROR` |
| 2 | any infrastructure error, or no tests ran | `EXECUTION_ERROR` |
| 3 | excluded tests > `max_excluded_fraction` (default 0.34) of the suite, or every failing test is excluded | `UNRELIABLE_EVIDENCE` |
| 4 | observation agrees with *R* on every reliable test | `NO_FAILURE_OBSERVED` |
| 5 | *C* = {Mᵢ : agree on **every** reliable test}; if *C* = ∅ | `UNMODELLED_BEHAVIOUR` (nearest models reported with their mismatch counts, not as a diagnosis) |
| 6 | \|C\| ≥ 2 | `AMBIGUOUS` (candidates listed; the tests that would distinguish them are named if the content has any) |
| 7 | \|C\| = 1 but *support* < `min_support` (default 2), where support = number of reliable tests on which *M* differs from *R* (i.e. failures it explains) | `INSUFFICIENT_EVIDENCE` |
| 8 | otherwise | `HYPOTHESIS_SUPPORTED` (M) |

The rationale record for every outcome contains: per-test observation vs. reference vs.
each model; excluded tests with reasons; candidate set; support count; for each rejected
model, the tests that contradict it; and the text "consistent with — not proof of — this
error; unmodelled explanations remain possible".

Properties this gives us, each covered by a unit test:

* A single weak, non-discriminating test cannot produce a diagnosis (rule 7).
* Two models that the suite cannot separate always yield `AMBIGUOUS`, never a pick (rule 6).
* A failing submission never gets forced into a category (rule 5).
* Unreliable evidence is never diagnosed (rule 3).

**Behaviour groups and qualified hypotheses (v1.1, ADR-019).** Tests that every modelled
program passes together or fails together form one *behaviour group*; they carry one
observation, however many there are. The rationale records `support_behaviours`, the
number of groups among the supporting tests. v1.1 keeps v1's decisions, and a supported
diagnosis resting on a single group is marked `evidence_strength = single_behaviour` with a
qualification ("other errors that produce the same behaviour cannot be ruled out"). The
candidate rule C6 (`v2-candidate`, `min_behaviours = 2`) extends rule 7 to
`support < min_support` **or** `groups < min_behaviours`; it is evaluated, not deployed.

**Not assessed: complexity.** The statements ask for O(log n), but no test, signature or
diagnosis checks it. The large tests (200 000 elements) only exercise scale: a linear scan
passes them, and wall time includes container start-up, so it cannot separate O(n) from
O(log n). No output of CodeAdapt may claim that a solution meets, or fails, a complexity
requirement until a separately validated mechanism exists (for example, counted
comparisons through an instrumented harness).

Strict consistency is deliberately conservative: a student whose code has *two* bugs, or
one modelled bug plus noise, gets `UNMODELLED_BEHAVIOUR`. That costs coverage, buys
precision, and is measurable. Later methods (e.g. likelihood scoring with an explicit
noise model, compositional error models) implement the same `DiagnosticMethod` protocol
and are compared on the same archived evidence.

## 5. Adaptive policy v1: transparent rules over an evidence ledger

**Learner evidence ledger.** For each learner and skill: the chronological list of probe
observations (test, problem, passed/failed, reliable?). No latent "mastery" variable.

**Selection rules** (`adaptation/policy_v1`), each producing a recorded rationale and a
**success criterion** (which future observations would count as improvement):

| Diagnosis | Next activity | Success criterion recorded |
| --- | --- | --- |
| `HYPOTHESIS_SUPPORTED(M)` | exercise from the problem family whose tests probe `M.skill` most densely and that the learner has not recently attempted | on the follow-up, all reliable tests probing `M.skill` pass, and the follow-up's diagnosis is not `M`'s analogue |
| `AMBIGUOUS(C)` | exercise whose test suite *discriminates* between the skills of the candidates | follow-up diagnosis resolves to one candidate's skill or to `NO_FAILURE_OBSERVED` on those probes |
| `NO_FAILURE_OBSERVED` | next exercise in the family whose probes have the least evidence in the ledger | follow-up passes its probes |
| `UNMODELLED` / `INSUFFICIENT` / `UNRELIABLE` | retry the same problem with the generic feedback; flagged for researcher review | none claimed (`not_comparable`) |
| `COMPILE_ERROR` / `EXECUTION_ERROR` | retry the same problem | none |

**Follow-up evaluation** compares, per probe of the targeted skill, the index attempt and
the follow-up attempt, and records `criterion_met` / `criterion_not_met` /
`not_comparable`, with the per-probe table. The UI wording is "passed all 4 tests related
to the recommended focus", never "mastered binary search".

**As implemented (M6).** `adaptation/policy_v1.py` and `adaptation/followup.py` are pure
functions; `worker/adapt.py` feeds them stored rows and stores their output in the
append-only `recommendations` and `followup_evaluations` tables.

* *Ledger.* Built from each attempt's diagnosis-rationale test table: a reliable test that
  matched the reference is `passed`, a reliable test that did not is `failed`, anything
  else is `excluded`. Passed and excluded tests are attributed to every skill their probes
  name. Since policy 1.1 (ADR-019, change C5) a failed test is skill evidence only when a
  supported diagnosis explains it, and then only for the selected model's skill; other
  failures are not attributed to any skill. In the demo bank all three problems probe the
  same four skills, so this changes the ranking's evidence counts but no ranking decision.
  Since policy 1.2 (ADR-023) the diagnosis must also be unqualified (two or more behaviour
  groups and no documented collision), and every attempt is attributed with the skill-map
  snapshot of its own content version; a version without one contributes nothing.
* *Skill observations (learner-model input, ADR-023).* `skill_observations` reduces each
  attempt to at most one `correct` or `incorrect` observation per skill, under the rules of
  docs/component-interfaces.md §5. Nothing consumes them yet; they are the contract a
  learner model will read.
* *Qualified hypotheses.* When the diagnosis is single-behaviour or the model has a
  `known_limitation`, the recommendation records `qualified_hypothesis` and the student
  wording says the pattern has more than one possible cause. The target is the skill.
* *Candidate problems* are those in the same `family` as the index problem. Skills are
  linked across problems by key, which is a content-authoring assumption.
* *Recently attempted* means among the learner's last 3 attempts.
* `HYPOTHESIS_SUPPORTED(M)`: rank by (recently attempted, −tests probing `M.skill`, slug).
  If no problem probes the skill, retry the index problem.
* `AMBIGUOUS(C)`: rank by (−number of candidate skills the problem has error models for,
  recently attempted, −tests probing those skills, slug). The criterion is that every
  reliable follow-up test probing those skills passes.
* `NO_FAILURE_OBSERVED`: among family problems without a no-failure attempt by this
  learner, rank by (recently attempted, reliable ledger entries for the problem's skills,
  slug). When none remain the action is `none`; this is explicitly not a claim of
  complete understanding.
* A learner's *open* recommendation is their latest one without an evaluation. The first
  later attempt on the recommended problem is the follow-up. Compile and execution errors
  neither consume nor replace an open recommendation for the same problem; an attempt on
  a different problem supersedes it without a verdict; an attempt created before the
  recommendation existed is not its follow-up.
* Verdicts: `not_comparable` when no criterion was recorded, when the follow-up's outcome
  is `UNRELIABLE_EVIDENCE` (or a compile/execution error), or when no reliable follow-up
  test probes the targeted skills; `criterion_not_met` when any such test failed or the
  follow-up is diagnosed with an error model of an excluded skill; otherwise
  `criterion_met`.

* *Relation (criterion_check 1.1).* Each evaluation records how the follow-up problem
  relates to the index problem: `same_problem` (a retry, whose failing tests the student
  has seen), `equivalent_practice` (a linked equivalent or the same family), `transfer` (a
  linked transfer problem) or `other`. These are different kinds of evidence and are never
  pooled. Equivalent practice and later transfer problems stay in the plan
  (docs/content-design, gaps G1–G3); the demo bank has no transfer problem yet.

**What a verdict does not mean.** `criterion_met` says the follow-up passed its targeted
tests. It is equally consistent with learning, with the follow-up problem being easier, and
with outside help; there is no comparison condition. It is not mastery, and on a problem
linked as transfer, one passing attempt is not demonstrated transfer. The scripted synthetic trajectories in
`tests/unit/test_trajectories.py` check the mechanics of these rules and nothing about
their effect on learners.

### Learner model LM1: researcher-only BKT (ADR-025)

`codeadapt.learner.bkt` traces each skill with standard Bayesian knowledge tracing, using
only `skill_observations()` (§5 and docs/component-interfaces.md §6).

**What it is.**
- **Parameters:** one parameter set, `bkt-params-assumed-1`, for every skill: P(L0) = 0.3,
  P(T) = 0.1, P(G) = 0.2, P(S) = 0.1. These are the author's placeholder values. They are
  not fitted, not taken from validated learner data and not calibrated. The set enforces
  0 < p < 1 and P(G), P(S) < 0.5.
- **Update:** each counted observation is conditioned by Bayes' rule, then the learn
  transition is applied. The reported P(known) is the value after the last counted
  observation and its transition.
- **Counting (owner decision L1):** only the first reliably evaluated attempt on each
  problem *version* counts. Compile errors, execution errors and unreliable evidence do not
  use up that attempt. A later attempt on the same version is a retry after feedback; its
  observations stay listed as uncounted, with a reason. An abstaining first attempt
  (ambiguous, unmodelled, insufficient) does use it up, because the learner saw its
  feedback.
- **Display threshold:** no value is shown below 3 counted observations from 2 distinct
  problems. Problems are counted by identity (slug), so several versions of one problem
  count once, while each observation keeps its exact version.
- **Why the threshold:** it controls display only. Meeting it says nothing about whether
  the estimate is accurate.

**Where it is visible.** Only in the researcher console (`/research/learners/<user>`,
API `GET /api/v1/research/learner-model`), always labelled "estimated under assumed
parameters". No student response and no policy reads it. Feedback, diagnosis and
recommendation are unchanged.

**Assumptions and limits kept explicit.**
- Standard BKT assumes independent skills, no forgetting, and the same parameters for
  every problem. None of these has been checked here.
- Observations are derived from author-written tests through an author-assigned skill
  map:
  - a `correct` observation means every reliable probing test passed, which can happen by
    coincidence (weak evidence);
  - an `incorrect` observation means an unqualified supported diagnosis, which is a
    behavioural pattern, not proof of a misconception.
- Counting per version means a learner who meets a revised version of a problem gets a
  new counted attempt, although they may remember the earlier one.
- With three demo problems, every estimate is dominated by its prior.
- The tests check the arithmetic and the rules on synthetic attempts. They are not
  evidence about real learners.

### Why not fitted knowledge tracing or learned classifiers now

**Direction (ADR-021).** Bayesian knowledge tracing is part of the intended architecture,
as a learner model between the skill-evidence layer and the recommendation policy, while
fingerprint diagnosis stays the diagnostic engine. LM1 above implements it with assumed
parameters. The table lists what is needed before the parameters are more than
assumptions, or before the estimates may drive anything.

| Method | Value | Prerequisite we don't yet have | Earliest sensible milestone |
| --- | --- | --- | --- |
| BKT / programming knowledge tracing | principled skill-state estimate over many attempts | many attempts per learner per skill; a validated probe→skill Q-matrix; real data to fit and check parameters | after a real cohort study (post-M9) |
| Learned diagnosis classifier / code embeddings | coverage of unmodelled errors | labelled real submissions; risk of opaque decisions conflicts with explainability | only as a *candidate generator* reviewed against evidence, post-M9 |
| Bayesian fingerprint scoring | graded support under noise | a noise model estimated from real data | M7+ as a research comparison against v1 |

## 6. Evaluation plan

### 6.1 Synthetic (what we can evaluate honestly without students)

Ground truth: submissions whose bug is *known by construction*.

* **Development set:** the error-model mutants themselves (sanity only — trivially
  matched, never reported as accuracy).
* **Held-out set:** independently written buggy variants per error model (different
  style, variable names, loop forms), plus *distractors* — correct alternatives, bugs
  outside the model, and double bugs. Authored before running the method; stored under a
  separate `eval/` content path with `data_class = synthetic`.

Metrics (per problem and overall, with counts, not just ratios):

| Metric | Definition |
| --- | --- |
| Coverage | fraction of failing held-out cases that receive `HYPOTHESIS_SUPPORTED` |
| Selective accuracy | among diagnosed cases, fraction whose diagnosis equals the ground-truth error model |
| Abstention rate, by reason | fraction per abstaining outcome |
| False-positive diagnoses | diagnosed cases whose truth is a different model, an unmodelled bug, or correct code |
| False negatives | modelled-bug cases that abstained (cost of conservatism) |
| Suite discrimination | number of model pairs with identical fingerprints (indistinguishable); minimal distinguishing tests |
| Reproducibility | fraction of identical observations across repeated runs and across environments (e.g. runc vs runsc, two hosts) |

Limitations stated with every report: synthetic bugs come from the same authors as the
model; held-out ≠ real-world distribution; selective accuracy here is an *upper bound*
on what real students' code will show.

**As implemented (M7).** `codeadapt-eval` (`backend/src/codeadapt/evaluation/`) loads
`eval/heldout/<problem>/cases.toml`, measures each problem's fingerprints, validates the
content, then runs every case through the same evidence collection
(`evidence/collect.py`) and diagnostic method as the worker, twice by default. It writes
JSON and Markdown reports containing no timestamps, so two runs can be compared byte for
byte. Definitions as computed:

* *Buggy* cases are those whose truth is not `correct`; *modelled-bug* cases are those
  whose truth is an error-model key.
* Coverage = buggy cases diagnosed / buggy cases. Selective accuracy = diagnoses equal to
  the truth / diagnoses. False negatives = modelled-bug cases not diagnosed / modelled-bug
  cases. Correct code is reported separately as cases with `NO_FAILURE_OBSERVED`.
* Reproducibility = cases whose outcome, selected model and every observed test
  signature were identical across the repeated runs, in one environment. Cross-environment
  reproducibility (runc vs runsc, two hosts) is not measured yet; it needs M8's gVisor host.
* Suite discrimination is taken from content validation: identical model pairs, and the
  number of tests detecting each model.
* A ratio with a zero denominator is printed as `n/a`, never as 0% or 100%.

The 2026-10-15 report is in [evaluation/synthetic-2026-10-15.md](evaluation/synthetic-2026-10-15.md).
Its 14 new held-out cases were written before the method was run on them; the other 3
date from M3 and had been run before. Several held-out cases are close in algorithm to
their error model (for example, `classic_exact_search.cpp` is the same textbook search
as `exact_match_sentinel`), which makes those diagnoses easy. That is a weakness of the
set, not evidence of robustness.

### 6.2 Real students (needs owner/institution input)

Only with consent and ethics approval. Adds: agreement of diagnoses with blinded expert
labels on a sample (selective accuracy on real data, inter-rater agreement); follow-up
improvement rates with a comparison condition (e.g. targeted vs. generic next exercise);
recommendation acceptance. Synthetic results are never presented as evidence of learning
effectiveness.
