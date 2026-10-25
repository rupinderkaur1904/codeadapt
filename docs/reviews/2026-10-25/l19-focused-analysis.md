# L19 focused analysis: rule C, option B and the 421 synthetic programs (2026-10-25)

**Status.** This is analysis only, as the owner asked on 2026-10-25 at 07:52. **Rule C is
unchanged.** No change was made to:

- the evidence rules or the BKT parameters;
- the skill mappings or any threshold;
- any historical evaluation result.

Option B is **not approved**. Every number here comes from committed records, and nothing was
re-executed. To reproduce:

```
python3 docs/reviews/2026-10-25/l19_breakdown.py   # this analysis
python3 docs/reviews/2026-10-25/l19_measure.py     # the earlier per-problem summary
```

## 1. Exact current behaviour (rule C)

`skill_observations()` in `backend/src/codeadapt/adaptation/ledger.py` gives **at most one
observation per (attempt, skill)**, using the skill map of the attempt's own content version.

1. **No observations at all.** This applies when the attempt is a compile error, an execution
   error or unreliable evidence, or when it has no skill map.
2. **`incorrect` on the model's skill.** The diagnosis must be `hypothesis_supported`, with a
   model the skill map knows. It must not be qualified (`single_behaviour`), and the model must
   not be a documented collision (`known_limitation`). The observation's basis is "supported
   diagnosis: <model>".
3. **`correct` on any other skill S.** This is **rule C**. It needs at least one test of the
   attempt that probes S, and every test probing S must be `PASSED`. A failed or excluded test
   probing S means S gets nothing. The basis is "every reliable test probing the skill passed".
4. **Nothing else.** In every other case the skill gets no observation.

**Step 3 ignores the diagnosis outcome.** It applies the same way to:

- passing attempts;
- named attempts, qualified or not;
- `unmodelled_behaviour`, `ambiguous` and `insufficient_evidence`;
- `non_termination_observed`.

So a failing attempt that is not named can never produce `incorrect`, but it can produce
`correct` on every skill whose probing tests it happened to pass.

**BKT (LM1).**

- **Which attempts count.** Only the first reliably evaluated attempt per (problem, content
  version) is counted, through `counted_attempts`. An abstaining attempt counts, because it is
  reliably evaluated. Compile errors, execution errors and unreliable attempts do not use up
  the opportunity. Later attempts are listed as retries and not counted.
- **Updates.** Each counted observation is conditioned by Bayes' rule, then the learning
  transition is applied. A skill with no observation is not updated.
- **Display threshold.** A value is shown from 3 counted observations on 2 distinct problems.

## 2. Exact difference under option B (not approved)

Option B changes **step 3 only**, and only for one kind of attempt.

**When it applies.** The attempt has at least one reliable failed test, and it did not satisfy
step 2. That covers the outcomes `unmodelled_behaviour`, `ambiguous`, `insufficient_evidence`
and `non_termination_observed`, and a qualified named diagnosis.

**What changes.** Such an attempt gives **no observations at all**, neither `correct` nor
`incorrect`.

**What does not change.**

- Passing attempts (`no_failure_observed`).
- Unqualified named attempts. They keep step 2, and step 3 for their other skills.
- Compile, execution and unreliable outcomes, which already give nothing.

**Counting.** Option B as proposed keeps the LM1 counting rule. So an abstaining first attempt
**still uses up** the counted opportunity, and now contributes nothing. The learner's later
correct retry on the same version stays uncounted. That learner therefore gives **zero
observations** from that problem version.

Letting an abstaining attempt not use up the opportunity is a separate question. It would
reverse the owner's confirmation of 2026-10-17, so option B does not include it.

## 3. How failing attempts that are not named affect evidence and BKT now

**Effect on P(known).** Under `bkt-params-assumed-1` (P(L0) = 0.3, P(T) = 0.1, P(G) = 0.2,
P(S) = 0.1), P(known) starts at 0.3. These are assumed parameters, not fitted.

| Counted observations | P(known) after |
| --- | --- |
| one `correct` | 0.693 |
| two `correct` | 0.919 |
| three `correct` | 0.983 |
| one `incorrect` | 0.146 |
| `incorrect`, then `correct` | 0.491 |
| `correct`, then `incorrect` | 0.298 |

**The worked example.** A failing, abstained count-occurrences attempt that earns
`problem_specification = correct` moves that skill from 0.3 to 0.693. The same attempt under
option B leaves it at 0.3. Because the attempt is counted, it also brings the skill closer to
the display threshold.

**Effect on the ledger and the research views.** These are unchanged by either option. A failed
test is recorded in the ledger only under a model explaining it in an unqualified way, so
failing attempts that are not named already add no failure entries. Their passing tests do
appear in the ledger under their probes' skills.

## 4. Breakdown of the 421 synthetic incorrect programs (v1.3)

**The corpus.** These are the VAL1-A mutants (lower-bound) and the VAL1-A2 mutants
(count-occurrences, last-less-than, first-true) labelled `incorrect_failing`. They are
single-edit synthetic mutants.

| Outcome | Programs | No observation | `correct` only | `incorrect` only | `incorrect` + `correct` | `correct` obs | `incorrect` obs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| named, unqualified | 28 | 0 | 0 | 23 | 5 | 5 | 28 |
| named, qualified (single behaviour or documented collision) | 12 | 2 | 10 | 0 | 0 | 14 | 0 |
| `insufficient_evidence` (rules 8a/8b) | 20 | 10 | 10 | 0 | 0 | 10 | 0 |
| `unmodelled_behaviour` | 248 | 188 | 60 | 0 | 0 | 65 | 0 |
| `non_termination_observed` | 113 | 113 | 0 | 0 | 0 | 0 | 0 |
| **All** | **421** | **313** | **80** | **23** | **5** | **94** | **28** |

**Reading the table.**

- **313 programs (74%) produce no observation at all.** Of the 108 that produce any, 80
  produce only `correct`.
- **How many `correct` observations per program:** 336 programs have none, 76 have one, and 9
  have two.
- **No `ambiguous` outcome** occurred in this corpus under v1.3.
- **Non-termination earned no `correct` in this corpus.** Each of these programs failed (or had excluded) at
  least one test probing every skill. That is a property of these mutants, not a rule.

**Under option B**, the rows "named, qualified", `insufficient_evidence`,
`unmodelled_behaviour` and `non_termination_observed` would all move to "no observation". That
removes **89 `correct` observations** (14 + 10 + 65) and **0 `incorrect`**. The named,
unqualified row keeps all 5 + 28.

## 5. Were the 94 and 28 checked against independent labels? No.

**Both numbers are counts of what the system's own attribution rules produced.** They are not
accuracy figures, and neither was scored against an independent, skill-level ground truth.

- **The only labels that exist** are the VAL1 behavioural labels. A script computed them
  natively and committed them before the pipeline ran. A label is `model:<key>` when the
  mutant's output is identical to that error model on the label inputs, and `none` otherwise.
  They are not human labels, and they are not skill labels.
- **318 of the 421 programs are labelled `none`.** For them no reference exists against which a
  skill observation could be judged. 60 of them produce 65 `correct` observations, which
  **cannot be assessed**.
- **103 programs carry a model label.** Taking that model's skill as a proxy:
  - **The 28 `incorrect` observations** all fall on the labelled model's skill. This agreement
    is **close to circular**: the label means "behaves exactly like model X", and a named
    diagnosis selects the model whose behaviour matches.
  - **The 29 `correct` observations from labelled programs** (5 named, 24 not named) **never
    fall on the labelled model's skill**. So no `correct` observation contradicts its program's
    behavioural label.
  - **That is not the same as support.** For example, 9 mutants behave like
    `upper_uses_strict`, which prints 0 everywhere. Each earns `problem_specification = correct`
    only because 0 is the right answer for an absent target.
- **The underlying difficulty.** A mutant is a known one-line edit, but which *skill* that edit
  reflects is a human judgement that nobody has made. Without such labels, no rate of
  "correct observations that are right" can be computed.

## 6. The trade-off

**Avoiding unsupported observations.** Option B removes the 89 positives that rule C gives to
failing programs that are not named. They are 95% of all positives from wrong programs in this
corpus (89 of 94). Positives would then outnumber negatives from wrong programs by 5 to 28,
instead of 94 to 28. Option B adds no new threshold or parameter.

**Less learner-model evidence.** The scale of the loss depends on what real learners submit,
which is unknown.

- **On this corpus**, observations from wrong programs fall from 122 to 33 (−73%). Correct
  programs are unaffected.
- **Some removed positives may be genuine.** A partially correct program may really handle the
  skills it is credited with. With no skill labels (section 5), the proportion is unknown.
- **The counting rule compounds the loss** (section 2). An abstained first attempt still uses
  up the problem version, so for that learner the problem gives no observation at all.
- **Observation capacity is already thin.** The CE1.4 report shows how sensitive P(known) is
  when there are few observations. Fewer observations mean more skills shown as
  `insufficient_data` for longer.
- **Not affected:** what students see, diagnoses, recommendations (policy 1.4 does not read
  BKT), and research traces.

**In short.** Rule C trades possibly unsupported positive evidence for more evidence. Option B
trades less evidence for evidence that rests only on passing attempts and on unqualified named
diagnoses. Neither choice can be shown to make estimates more accurate without real data. The
argument for B is about consistency: it treats abstention as "no evidence" in both directions.

## 7. Tests required to verify option B, if approved

The implementation would be a new, selectable version of the evidence rules. Rule C would stay
selectable, as with the method versions v1.1 to v1.3.

**Unit tests** (`tests/unit`, ledger and learner model):

1. **Old rules unchanged.** The current rules give exactly the current observations for every
   existing fixture. The L19 assertion stays pinned for the old version.
2. **B, abstaining outcomes.** For each of `unmodelled_behaviour`, `ambiguous`,
   `insufficient_evidence` and `non_termination_observed`, and for a qualified named diagnosis,
   an attempt with at least one reliable failed test gives no observations. That includes skills
   whose probing tests all passed.
3. **B, other outcomes unchanged.** A passing attempt still gives `correct` on every probed
   skill. An unqualified named attempt still gives `incorrect` on its model's skill and `correct`
   on fully passing other skills. Compile, execution and unreliable outcomes still give nothing.
4. **B, edge cases.**
   - Excluded tests: a failing, not-named attempt whose only failures are excluded counts as
     `unreliable_evidence` (rule 3), not under B. An attempt with excluded tests and a reliable
     failure follows B.
   - Documented collision: a model with `known_limitation` behaves like a qualified diagnosis.
5. **Counting.**
   - Under B, an abstaining first attempt still uses up the problem version, with no
     observations.
   - The later correct retry is listed as uncounted with its retry reason.
   - Compile, execution and unreliable attempts still do not use it up.
6. **BKT.** A skill with no counted observation keeps P(L0). The display threshold counts only
   counted observations. The parameter set and label are unchanged.
7. **Version recording.** Every learner-model response and trace names the evidence-rule version
   used, and each historical record keeps the version it was computed with.

**Integration and sandbox tests:**

8. **The end-to-end adaptation test** (`test_adaptation_end_to_end.py`). Under B, the abstained
   count-occurrences attempt gives no observation, and everything else in the scenario is
   unchanged. Under the old rules, the existing assertion stays.
9. **Recommendations unchanged.** Policy 1.4 golden tests and recommendation outputs are
   identical under both versions.

**Replay and reports:**

10. **Case-by-case replay** from recorded evidence over held-out, calibration, VAL1-A and
    VAL1-A2. For every case it would show:
    - the old-version observations reproduced exactly;
    - the B observations;
    - a per-outcome loss table matching section 4 (89 `correct` removed, 0 `incorrect`).
11. **CE1.4 rerun.** Observation capacity and BKT sensitivity, recomputed under B as a separate
    new report. The original report is preserved.
12. **Docs and CI.** Updated L19 entry and methodology text, and green CI on every job.
