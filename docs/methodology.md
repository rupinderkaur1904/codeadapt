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
| `time_limit` | CPU or wall limit exceeded |
| `memory_limit` | killed by the memory cgroup |
| `output_limit` | exceeded output cap |
| `infrastructure_error` | sandbox failure — not evidence about the program |

**Reliability marking.** A test observation is excluded (and listed as excluded, with the
reason) when:

* the sanitiser build (`-fsanitize=address,undefined`) reports a finding on that test →
  undefined behaviour, output not trustworthy;
* a repeated run of the test produces a different signature → non-determinism;
* the observation is an `infrastructure_error`.

UB found by the sanitiser is itself reported to the student as an actionable finding
("reads past the end of the array on some inputs"), separately from the diagnosis.

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
| `HYPOTHESIS_SUPPORTED(M)` | exercise from the catalogue whose tests probe `M.skill` most densely and that the learner has not recently attempted | on the follow-up, all reliable tests probing `M.skill` pass, and the follow-up's diagnosis is not `M`'s analogue |
| `AMBIGUOUS(C)` | exercise whose test suite *discriminates* between the skills of the candidates | follow-up diagnosis resolves to one candidate's skill or to `NO_FAILURE_OBSERVED` on those probes |
| `NO_FAILURE_OBSERVED` | next exercise in the family whose probes have the least evidence in the ledger | follow-up passes its probes |
| `UNMODELLED` / `INSUFFICIENT` / `UNRELIABLE` | retry the same problem with the generic feedback; flagged for researcher review | none claimed (`not_comparable`) |
| `COMPILE_ERROR` / `EXECUTION_ERROR` | retry the same problem | none |

**Follow-up evaluation** compares, per probe of the targeted skill, the index attempt and
the follow-up attempt, and records `improved` / `not_improved` / `not_comparable`, with
the per-probe table. The UI wording is "passed all 4 boundary-condition checks on the
follow-up exercise", never "mastered binary search".

### Why not BKT / knowledge tracing / learned classifiers now

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

### 6.2 Real students (needs owner/institution input)

Only with consent and ethics approval. Adds: agreement of diagnoses with blinded expert
labels on a sample (selective accuracy on real data, inter-rater agreement); follow-up
improvement rates with a comparison condition (e.g. targeted vs. generic next exercise);
recommendation acceptance. Synthetic results are never presented as evidence of learning
effectiveness.
