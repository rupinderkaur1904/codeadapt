# Proposal: milestone LM1, a first Bayesian learner model (for owner review)

Status: **proposed, not implemented** (2026-10-17). No learner-model code exists. This
follows ADR-021 (a separate, testable BKT milestone once the evidence layer is reliable)
and contract 3 of docs/component-interfaces.md §6. EV1 (ADR-023, ADR-024) delivered the
input it needs: `skill_observations()`.

## 1. Scope

LM1 adds standard Bayesian knowledge tracing (BKT), one independent model per skill, as a
pure function over one learner's `SkillObservation` stream. Its estimates are visible only
in the researcher console. The student never sees them, and the recommendation policy does
not read them. Policy v1.2 and the student feedback stay exactly as they are.

Not in LM1:
- policy changes;
- fitting parameters to data (there is no real data to fit);
- persisting estimates (they are recomputed from stored observations, so no migration is needed);
- showing anything to students;
- new content.

## 2. Model

The model is standard BKT with four parameters per skill:
- P(L0): prior;
- P(T): learn;
- P(G): guess;
- P(S): slip.

It has no forgetting. After an observation the posterior is updated by Bayes' rule, then the learn transition is applied.

**Parameters are assumptions.** LM1 uses one placeholder set for all four skills:

| P(L0) | P(T) | P(G) | P(S) |
| ---: | ---: | ---: | ---: |
| 0.3 | 0.1 | 0.2 | 0.1 |

These numbers are the author's choice. They are not derived from data or from a validated source. They are stored as a versioned parameter set (`bkt-params-assumed-1`), and every output names that set.

LM1 also enforces the usual non-degeneracy constraint, P(G) < 0.5 and P(S) < 0.5, so that a `correct` observation can never lower the estimate.

## 3. Input rules

The model reads only `skill_observations()`. Ambiguous, unmodelled, qualified, inconclusive, infrastructure and compile-error attempts never produce observations, so the model never sees them.

One open question stays: repeated attempts on the same problem are not independent. A second submission made after seeing feedback is weaker evidence than a first attempt. **Decision L1** below sets which observations update the estimate.

## 4. Output contract (component-interfaces §6)

The model produces one result per skill. Each result contains:
- P(L) after the last counted observation;
- the counted observations and the uncounted ones, each uncounted one with its reason;
- the number of distinct problems behind the counted observations;
- the model version and the parameter-set version.

The state is `insufficient_data` until the skill has at least 3 counted observations from at least 2 distinct problems. Everything the console shows is labelled "estimated under assumed parameters". The words "mastered" and "mastery level" are never used.

## 5. Acceptance criteria

1. **Update arithmetic:** unit tests check the update against values worked out by hand for a short sequence, for both observation values.
2. **Property tests over the existing synthetic trajectories:**
   - a `correct` observation never lowers P(L) and an `incorrect` one never raises it before the transition;
   - estimates stay in [0, 1];
   - the result depends only on the observation stream.
3. **Excluded evidence:** an attempt producing no observation leaves every estimate unchanged. This is tested with an inconclusive attempt, a qualified diagnosis and a compile error.
4. **Content-version identity:** each observation keeps its content version, and an attempt on a version without a skill-map snapshot contributes nothing.
5. **Insufficient data:** `insufficient_data` is reported below the threshold. A test also checks that observations from a single problem never leave this state.
6. **Researcher console:** it shows the estimate, the observation provenance, the parameter set and the "assumed parameters" label. Student API responses are unchanged, and an existing API test is extended to check this.
7. **Docs:** methodology, ADR-025 and roadmap are updated. Any synthetic run is reported as an implementation test, never as calibration or a learning gain. CI is green.

## 6. Decisions for the owner

| ID | Question | Recommendation |
| --- | --- | --- |
| L1 | Which observations update the estimate? (a) only the first attempt on each problem version; (b) every attempt; (c) the first attempt, plus later attempts only when they are `incorrect` | **(a)**. It is the most conservative, it is simple to explain, and later attempts stay visible as uncounted with reason "retry". Its cost is that with three problems each skill gets at most three counted observations. |
| L2 | Accept the placeholder parameters in §2, labelled as assumptions | accept |
| L3 | Estimates visible only to researchers in LM1 | yes |
| L4 | Build LM1 now, or extend content (CE1) first | **LM1 now, as researcher-only plumbing.** With 3 problems and 4 skills, every estimate will be dominated by its prior (risk 9 in §9 of component-interfaces), so LM1 tests the contract end to end, not the learner. Content expansion (CE1) is what makes estimates informative. |

## 7. Risks

- Observations based on passing tests are weak evidence (component-interfaces §9, risk 5). BKT treats them as fully informative, softened only by P(G).
- The skill mapping is the author's assumption. A wrong mapping becomes a confident wrong estimate.
- Standard BKT assumes the skills are independent, that there is no forgetting, and that parameters are the same for every problem. None of these assumptions has been checked.
- None of this is validated on real students.
