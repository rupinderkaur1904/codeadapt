# State assessment and next milestone (2026-10-17)

Reconstructed from the repository at commit `4ea77f0` on `claude/project-thread-cezsmq`
(clean working tree). Categories: **implemented** (code exists), **tested** (automated
tests exercise it), **evaluated** (measured on synthetic, author-written cases),
**proposed** (documented, no code), **unverified** (claimed or hoped, not shown).
Nothing has been evaluated on real students.

## 1. Learning loop, step by step

| Step | State | Evidence | Gaps |
| --- | --- | --- | --- |
| 1. Problem with specification and objectives | implemented, tested | 3 demo problems (lower-bound 17 tests / 8 models, count-occurrences, last-less-than), 47 tests with declared purpose and `distinguishes` checked against measurement | one problem family (binary search); CE1 not started |
| 2. Execute submission | implemented, tested | Docker sandbox (runc), STANDARD + SANITIZE builds, repeat runs; 32 sandbox tests incl. adversarial ones; CI green on 8b3f4fa | production tier (gVisor) **not tested**; timeout classification gap (§2) |
| 3. Compare with executed fingerprints | implemented, tested, evaluated | fingerprints measured per (content version, environment) and validated; `fingerprint_consistency` 1.1 | — |
| 4. Hypothesis, ambiguity, abstention | implemented, tested, evaluated | outcomes `ambiguous`, `unmodelled`, `insufficient`, qualified; held-out 9/13 correct, 0 wrong, 0 false alarms; calibration 1 wrong of 2 (E2 clamp collision) | held-out cases written by the models' author, so not independent; E2 indistinguishable from a clamp by design |
| 5. Map reliable evidence to skills | implemented (policy 1.1), tested | failures count only when a supported diagnosis explains them (C5) | **C6 revision not implemented**: qualified diagnoses still add failure evidence; evidence is counted per test, not per behaviour; old attempts mapped through the current spec |
| 6. Update mastery estimates | **proposed only** (ADR-021, ADR-023) | no learner-model code, by decision | needs trustworthy, per-attempt observations first |
| 7. Select next exercise with reason and criterion | implemented, tested | `rule_policy` 1.1: family + skill-probe density, rationale, fixed success criterion, relation recorded | policy does not use curriculum prerequisites, difficulty or uncertainty; no prerequisite-support or reassessment choice |
| 8. Use later performance | implemented, tested | follow-up verdicts `criterion_met` / `not_met` / `not_comparable`; never "mastery" | — |

Platform: FastAPI + worker + React workspace and researcher console (M3–M7) implemented and
tested (browser e2e in CI). M8 (real auth, gVisor, deployment) and M9 (consent, study
protocol) not started; no public deployment.

## 2. Unresolved issues, in order of importance

1. **Execution evidence can misreport a stall as a program timeout.** Measured: under load
   a genuine infinite loop and a stalled trivial run both end at the wall deadline and get
   the same `time_limit` signature. The repeat rule catches a single stall, not two in a
   row. CI saw one such event (fingerprinting failed closed, no student evidence).
2. **Skill evidence is not yet what BKT needs.** Qualified diagnoses add failures; tests in
   the same behaviour group count as independent observations; old attempts use today's
   skill map. So the evidence layer cannot yet supply trustworthy, appropriately structured
   observations. **BKT is therefore not the next milestone.**
3. **Lost output (ADR-020) unconfirmed.** Never reproduced; the mismatch check may or may
   not catch it. The robust fix (end-of-output marker) changes every content version.
4. **Recommendation policy ignores the curriculum graph** (prerequisites, reassessment).
   Matters once the learner model exists; not a blocker before it.
5. **Validation limits.** No independently written held-out cases; no real-student data;
   one problem family.

## 3. Recommended next milestone: EV1, trustworthy skill evidence

Implement the evidence contracts of docs/component-interfaces.md (D1–D4), so that every
skill observation a learner model would consume is reliable, diagnosis-justified,
behaviour-level and tied to its content version. No Bayesian code.

Acceptance criteria:

1. **Timeouts (D1).** A CPU-limit stop is `time_limit` evidence. A wall-deadline-only stop is
   re-run once with a longer wall deadline; a second wall-only stop is excluded as
   `inconclusive`, never a failure. Applies to student runs and fingerprint measurement.
   Regression tests: scripted wall-only stall of a trivial program (fake docker) is never
   evidence; a real infinite loop is still a timeout, idle and under load (sandbox test).
2. **Infrastructure retries (D1).** Student runs re-measure infrastructure errors (bounded,
   same as fingerprinting); persistent ones still yield `execution_error`.
3. **Ledger policy 1.2 (D2).** Qualified diagnoses (one behaviour group or documented
   collision) add no failure evidence; the student-facing message is unchanged.
   Regression test on the E2 trajectory.
4. **Per-attempt skill observations (D3).** A pure function produces at most one
   `correct`/`incorrect` observation per (attempt, skill) under rule C, with identity and
   basis; tests in one behaviour group count once. Property tests over the existing
   trajectories.
5. **Version identity (D4).** A skill-map snapshot is stored per content version and every
   attempt is resolved through its own version; a migration backfills current versions;
   an attempt on a version without a snapshot contributes nothing. Test with two versions
   whose probes differ.
6. Held-out and calibration results unchanged (diagnosis is not touched); full suite and CI
   green; docs and ADR-023 updated from "proposed" to what was implemented, with measured
   results and remaining limits.

Not in EV1: end-of-output marker (D5, changes all content versions), BKT, policy changes,
new problems.

## 4. Decisions

Within my authority (routine, follow established direction): D1 (evidence
classification), D3 (directed by "same behaviour must not count as independent
evidence"), D4 (version integrity). D2 was approved in principle on 2026-10-17.

Needs your review before I do it: **D5**, the end-of-output marker, because it changes the
output contract and the version of every problem. I recommend doing it after EV1 as its
own small milestone.
