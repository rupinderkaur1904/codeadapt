# Component interfaces: diagnosis, skill evidence, learner model, recommendation

**Status (2026-10-17):** written as a proposal; D1–D4 (§10) were then implemented in
milestone EV1, and the sections below say so where it applies. D5 and the learner model are
not implemented. It implements ADR-021's sequencing step: the four components' contracts
are defined before any Bayesian code. A rule marked *current* is what the code does today;
a rule marked *proposed* is not implemented. Nothing in this document is evidence that any rule is accurate for real
students.

Owner decisions this builds on (2026-10-17): student-facing explanations keep diagnosis
v1.1; skill-evidence updates use the stricter distinct-behaviour rule (the C6 revision);
C1–C2 stay applied with their limitations documented; a timeout caused by load must never
become student-failure evidence; the original lost-output failure stays unconfirmed.

## 1. Principles

1. **No layer strengthens what it receives.** A qualified or abstaining result stays
   qualified or abstaining downstream. A layer may only add exclusions.
2. **Abstention is a value, not an error.** Every interface has an explicit "no
   evidence" result, and consumers must handle it.
3. **A diagnosis is not a misconception.** The engine reports that an execution pattern is
   consistent with a known implementation error. Skill evidence is a modelling assumption
   on top of that, and a learner estimate is a further assumption.
4. **Everything carries its identity** (§2), so any number can be traced back to the
   exact content, environment, method and rule versions that produced it.
5. **Excluded evidence is recorded, never deleted.** It stays in storage with its reason.
   It is withheld from the layers that would treat it as evidence.

## 2. Identity carried on every record

| Field | Meaning | Status |
| --- | --- | --- |
| `submission_id`, learner id | the attempt and its owner | current |
| `data_class` | synthetic, development or real (ADR-009); classes are never mixed in one model | current on submissions |
| `problem_slug`, `problem_version` | content version = sha256 over the problem's files | current |
| `environment` digest | compiler, image digest, runtime, kernel | current |
| `fingerprint_set_id` | the measured predictions used, keyed by (version, environment) | current |
| `method`, `method_version` | diagnostic engine version | current |
| `evidence_rules_version` | the execution-classification rules of §3 | current (EV1), in the diagnosis rationale |
| `skill_evidence_policy` | ledger policy 1.2 (§5) | current as `policy_version` |
| `learner_model`, `learner_model_version`, parameter set id | planned | **proposed** |

**Content-version identity rules.**

* *Current:* a submission is diagnosed only against fingerprints of its own content
  version, measured in the same environment. A version whose fingerprints fail validation
  yields no diagnosis (fail closed: the job fails, nothing reaches the ledger).
* *Gap before EV1:* the ledger resolved skills through the *current* spec by slug
  (`worker/adapt.py` builds `problems` by slug), so an old attempt is mapped with today's
  probes. It skips test keys that no longer exist, but a probe that changed meaning under
  the same key would be misattributed. C1–C2 did not change any existing test's probes, so
  no stored attempt is affected today.
* *Current since EV1 (V1):* store a skill-map snapshot per content version (test → probes → skills;
  model → skill; model `known_limitation`) in `problem_versions`, and resolve every attempt
  through its own version's snapshot. A version without a snapshot contributes no skill
  evidence.

## 3. Contract 0: sandbox runner → execution evidence

The runner reports per test run: status, exit code, signal, `timed_out` (host wall-clock
deadline fired), OOM flag, output caps, wall time, and the client/container exit-status
check (ADR-020). The question is which of these are evidence about the *program*.

### 3.1 Measurement (2026-10-17, this dev container, 4 vCPUs, runc)

24 concurrent runs per row, limits as deployed (CPU rlimit 2 s soft, wall deadline
cpu + 1 s = 3 s). Load = busy-loop processes on the host.

| Program, test | Host load | Result | Wall time min / median / max |
| --- | --- | --- | --- |
| reference, `duplicates_middle` | none | 24 × output | 241 / 292 / 315 ms |
| reference, `duplicates_middle` | 8 busy loops | 24 × output | 341 / 459 / 554 ms |
| reference, `duplicates_middle` | 16 busy loops | 24 × output | 352 / 500 / 669 ms |
| `no_progress_update` (infinite loop), `single_above` | none | 24 × time limit via **SIGXCPU** (CPU limit) | 2275 / 2317 / 2409 ms |
| same | 8 busy loops | 24 × time limit via **wall deadline** (killed, SIGKILL) | 3174 / 3253 / 3379 ms |
| same | 16 busy loops | 24 × time limit via **wall deadline** | 3223 / 3329 / 3407 ms |

What this shows: without load, a genuine infinite loop is stopped by its own CPU limit.
Under CPU contention the same loop is stopped by the wall deadline instead, which is
exactly how a load-induced stall of a trivial program is reported. Today both become the
same `time_limit` signature. CPU load alone did not make the trivial program exceed 0.7 s,
so it did **not** reproduce the CI event (a trivial `stops_at_first_match` run recorded as
a time limit). That event most likely came from a multi-second stall in container start-up
or the Docker daemon, which this measurement does not exercise.

### 3.2 Outcome classes (`evidence_rules_version` 1 in EV1; 2 adds the end-of-output marker, ADR-024)

| Class | Condition | Evidence about the program? |
| --- | --- | --- |
| `output` | exited 0, streams consistent | yes |
| `runtime_error` | non-zero exit or signal, not a resource limit | yes |
| `program_timeout` | stopped by its **CPU-time limit** (SIGXCPU): the program itself used ≥ 2 s CPU | yes |
| `memory_limit`, `output_limit` | cgroup OOM or output cap | yes |
| `inconclusive` | stopped by the **wall deadline** without reaching its CPU limit, after the re-run in R2 | **no**: excluded, flagged for review |
| `infrastructure_error` | container did not start, client/container exit disagreement, daemon unavailable | **no** |

Rules:

* **R1 (genuine timeout).** Only a CPU-limit stop is a program timeout. CPU time is charged
  to the program's own process, so host load cannot produce it. (A program that calls
  `exit(152)` itself would look the same; this is documented, not handled.)
* **R2 (wall-only timeout).** A wall-deadline stop without the CPU limit is not evidence
  yet. The test is re-run once, alone, with a longer wall deadline (CPU limit unchanged,
  start-up grace raised from 1 s to 10 s). If the re-run hits the CPU limit, the
  observation is `program_timeout`. If it completes, the re-run's result is the
  observation and both runs are stored. If it is again wall-only, the observation is
  `inconclusive`. The same rule applies to fingerprint measurement, so a model's predicted
  timeout is always a CPU-limit timeout.
* **R3 (infrastructure).** *Current:* a compile container that did not start requeues the
  job; any run-level infrastructure error makes the whole attempt `execution_error` (no
  diagnosis, no skill evidence); fingerprinting re-measures infrastructure errors up to 3
  times. *Since EV1:* student runs get the same bounded re-measurement (3 attempts) before
  the attempt is declared `execution_error`.
* **R4 (repeat rule, current).** Every failing test is run again; if the two signatures
  differ, the observation is excluded as non-deterministic. This is what kept the CI event
  out of student evidence: it happened during fingerprinting, one of two runs disagreed,
  and the content was rejected (fail closed). The remaining gap is two consecutive stalls,
  which R2 closes for timeouts.
* **R5 (lost output; superseded by ADR-024, which implements the marker in the runner).** A run that exits 0 with empty output, with client and
  container agreeing, is indistinguishable from a program that prints nothing. Only R4
  protects against it. The robust fix is a harness end-of-output marker (proposed in
  ADR-020): a run that exits 0 without the marker is an infrastructure error. It changes
  every problem's output contract and therefore every content version. **The original
  lost-output failure remains unconfirmed:** it was never reproduced, the ADR-020
  mismatch check may or may not catch it, and CI passing since then is not evidence that
  it is fixed.

Infrastructure and inconclusive results are stored with their reason and wall times, so
the rate of each per environment can be monitored. A rising rate is an operational alarm,
not a learner signal.

## 4. Contract 1: execution evidence → diagnostic engine (current)

**Input** (`DiagnosticInput`): content version, compile status, one `Observation` per test
(signature plus `excluded_reason`), reference predictions, and each error model's
predictions, all from the same fingerprint set.

**Output** (`Diagnosis`): method and version, `outcome`, `selected_model`, `candidates`,
`support`, and a researcher-facing rationale (tests, exclusions, behaviour groups,
`evidence_strength`, `qualification`).

**Uncertainty** is categorical, not probabilistic:

| Outcome | Meaning | Abstains? |
| --- | --- | --- |
| `compile_error`, `execution_error` | nothing ran usefully | yes |
| `unreliable_evidence` | too many exclusions, or every failure is excluded | yes |
| `no_failure_observed` | every reliable test matched the reference; not proof of correctness | no failure claimed |
| `unmodelled_behaviour` | no model explains the failures | yes |
| `ambiguous` | more than one model explains them equally | yes (candidates listed) |
| `insufficient_evidence` | one model fits but support is below the threshold | yes |
| `hypothesis_supported`, `evidence_strength = multiple` | one model fits, ≥ 2 tests in ≥ 2 behaviour groups | no |
| `hypothesis_supported`, qualified | one model fits, but only 1 behaviour group or the model has a documented collision | qualified |

The engine is deterministic for a given input and never sees learner history.

**Consumers.** The student-facing feedback reads the diagnosis directly and applies v1.1:
a qualified diagnosis is shown as "one possible cause to check, not the answer". The
skill-evidence layer applies the stricter rule in §5. These are two thresholds on the same
diagnosis by design (owner decision, 2026-10-17).

## 5. Contract 2: diagnosis → skill-evidence layer (ledger policy 1.2, implemented in EV1)

**Unit of evidence:** one `SkillObservation` per (attempt, skill), not one per test
(`adaptation.ledger.skill_observations`). Tests in the same behaviour group are not
independent, so counting them separately would overstate the evidence. Fields:
`submission_id`, `problem_slug`, `problem_version`, `created_at`, `skill`, `value ∈
{correct, incorrect}`, `basis` (which rule below), the contributing test keys, and the
attempt's ordinal on that problem (1 for the first attempt). The relation to an earlier
recommendation is stored with follow-up evaluations, not on the observation. Nothing
consumes these observations yet; policy v1 still ranks with the per-test ledger, which
applies the same 1.2 failure rule.

**Rules**, evaluated with the attempt's own skill-map snapshot (V1):

| Diagnosis | `incorrect` observation | `correct` observations |
| --- | --- | --- |
| compile or execution error | none | none |
| unreliable evidence | none | none |
| unmodelled, ambiguous, insufficient | none | per rule C below |
| supported, ≥ 2 behaviour groups, no documented collision | the selected model's skill only | per rule C, other skills |
| supported, qualified (1 group, or the model has `known_limitation`) | **none** (the student still sees the qualified hint) | per rule C, other skills |
| no failure observed | none | per rule C |

**Rule C (correct).** A skill gets a `correct` observation only if at least one reliable
test probes it, every test probing it passed, and none of its probing tests was failed,
excluded, inconclusive or an infrastructure error. Otherwise the skill gets no
observation from this attempt.

**Excluded from skill evidence** (all stay stored with their reason):

* failures not explained by a supported, unqualified diagnosis (unmodelled, ambiguous,
  insufficient, qualified);
* observations excluded for sanitizer findings or non-determinism;
* `inconclusive` and `infrastructure_error` runs (§3), and whole attempts with
  `compile_error`, `execution_error` or `unreliable_evidence`;
* attempts on content versions without a skill-map snapshot, or whose fingerprints failed
  validation;
* attempts of a different data class from the model being built;
* complexity: the O(log n) requirement is not assessed, so no skill evidence is derived
  from speed (a `program_timeout` is evidence of non-termination or extreme slowness only).

**Uncertainty at this layer** is carried as counts and provenance, not probabilities: the
number of observations per skill, which problems and versions they come from, and their
basis. No mastery value exists here.

**Change from policy 1.1:** 1.1 counts per test and lets a qualified diagnosis add
failures. Policy v1.1's recommendation ranking can keep reading the per-test ledger, so its
behaviour is unchanged except that qualified failures stop counting.

## 6. Contract 3: skill evidence → Bayesian learner model (LM1, researcher-only; ADR-025)

**Input:** the ordered `SkillObservation` stream of one learner, one data class. Nothing
else: no raw runs, no diagnoses, no excluded observations.

**Output, per skill:** an estimate with its uncertainty (for BKT, P(L) after the last
observation), the number and provenance of the observations behind it, the model and
parameter-set versions, and a state of `insufficient_data` until a minimum number of
observations from at least two distinct problems exists. The output is described as
"estimated under the model's assumptions". It is never "mastered" and never shown to the
student as a fact.

**Obligations** (from ADR-021): the prior, learn, guess and slip parameters are
documented as assumptions until validated on real data; synthetic experiments may test
the implementation but are never reported as calibration or learning gains; repeated
attempts on the same problem are not independent, so the milestone must state how
`relation` and the attempt ordinal are used (for example, a retry after the student has
seen the failing tests may not count as a fresh `correct`).

## 7. Contract 4: → recommendation policy

**Input:** the latest diagnosis (to pass on qualification and target the follow-up), the
skill-evidence counts (today) or the learner-model state (later, including
`insufficient_data`), the curriculum links, and the catalogue.

**Obligations (current, kept):** a qualified diagnosis produces a qualified
recommendation; abstentions produce no targeted claim and set the review flag; a
follow-up is judged only against a criterion fixed when it was recommended, with verdicts
`criterion_met`, `criterion_not_met` or `not_comparable`; a follow-up result is never
called mastery or transfer. When the learner model exists, the policy may use its
estimates only to choose activities. It must not present them to the student as a
measurement.

## 8. Uncertainty across the layers

| Layer | Representation | "No evidence" value |
| --- | --- | --- |
| Runner | outcome class with reason | `inconclusive`, `infrastructure_error` |
| Reliability | per-test `excluded_reason` | excluded observation |
| Engine | categorical outcome, behaviour-group count, qualification | the abstaining outcomes |
| Skill evidence | counts and provenance of `correct` / `incorrect` per skill | no observation |
| Learner model | posterior estimate plus observation count, under stated assumptions | `insufficient_data` |
| Policy | recommendation with rule, rationale, review flag | `abstained`, `not_evaluated` |

## 9. Remaining risks

1. **Lost output occurs; its cause is unknown** (R5, ADR-024). CI showed it again on
   2026-10-17. The runner's end-of-output marker now turns such a run into an
   infrastructure error, but that is shown only against a scripted reproduction, not yet
   against a real recurrence. Partial loss that keeps the marker would not be caught.
2. **R2 is not tested against the real CI event.** The event was not reproduced, so R2 is
   a mitigation by construction. The timeout distinction itself is measured (§3.1).
3. **Wall-only timeouts of genuinely slow programs** become `inconclusive` if they stall
   twice. They lose evidence rather than gaining false evidence, but a heavily loaded host
   could exclude many timeouts and push attempts into `unreliable_evidence`.
4. **The skill mapping is an author's assumption** (probes, model → skill). It has not been
   checked against expert labels or real submissions.
5. **Passing tests are weak evidence** of a skill: a test can pass by coincidence, and
   probe coverage differs by problem.
6. **Behaviour groups depend on the modelled errors.** Adding a model can split a group
   and change a diagnosis's strength, so the evidence rule depends on content version
   (handled by identity, §2, but results are not comparable across versions without care).
7. **Unmodelled errors** that mimic a modelled one (E2 vs. a clamp) remain undetectable by
   behaviour; policy 1.2 only stops them from updating skills.
8. **Single-attempt independence.** The learner model must handle retries and practice
   effects; BKT's standard assumptions do not.
9. **Data volume.** With three demo problems, a learner model would see very few
   observations per skill; any estimate would be dominated by its priors.
10. **No real-student data.** None of these rules has been validated on real students.

## 10. Decisions requested

**Outcome (2026-10-17):** D1–D4 implemented in milestone EV1 (ADR-023 status). D5 was
replaced by ADR-024: CI then showed the lost-output failure again (exit 0, empty stdout,
exit statuses agreeing), and the marker was added in the runner instead of the harness, so
no content version changed. A further limit found while implementing: a gVisor (`runsc`) host has
not been tested, and R1 assumes it delivers SIGXCPU from the CPU rlimit; if it does not,
genuine timeouts there become `inconclusive` (lost, not invented).

| ID | Proposal | Recommendation |
| --- | --- | --- |
| D1 | Adopt evidence rules R1–R3 (CPU-limit timeouts are evidence; wall-only timeouts are re-run, then `inconclusive`; bounded infrastructure re-measurement for student runs) before any learner model consumes runner outcomes | adopt |
| D2 | Ledger policy 1.2 (§5), with qualified diagnoses (one behaviour group **or** a documented collision) producing no `incorrect` observation | adopt |
| D3 | One skill observation per (attempt, skill) for the learner model, while policy v1 keeps its per-test counts | adopt |
| D4 | Skill-map snapshot per content version (V1) | adopt |
| D5 | Harness end-of-output marker (R5); changes every content version | adopt, as a separate change after D1–D4 |

Proposed order after approval: D4, D1 and D2 with regression tests (including a scripted
wall-only timeout and a stalled trivial run), then D3, then D5. The BKT milestone proposal
comes after these, as ADR-021 requires.
