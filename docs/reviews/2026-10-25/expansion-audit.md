# Audit of the 25-problem bank (2026-10-25)

**Scope.** This is an audit only. Nothing in it changes:

- the recommendation policy (1.4);
- skill mappings;
- fingerprint rules or thresholds;
- rule C (L19), ADR-032 or L20;
- BKT parameters;
- any content version.

No problem was added. Synthetic, author-written results are labelled as such throughout.

## 1. Verified revision

| Item | Result |
| --- | --- |
| Branch, working tree | `claude/project-thread-dyivyy`, clean; local HEAD = remote HEAD |
| Audited commit | `ed35cf7` (the commit the owner named) |
| GitHub CI on `ed35cf7` | Run 112: **all 16 jobs succeeded**. The `demo-content` shards cover all 25 problems; they took 27.5 min under runc and 20 min under gVisor. |
| Local, same tree | unit 452 passed; ruff, format, mypy clean; web 34 tests, lint, typecheck, build ok; Playwright 3/3 (2.5 min) |
| Problem bank | 25 directories: binary-search 12, arrays 5, two-pointers 3, sliding-window 3, prefix-sums 2. `GET /api/v1/problems` returns 25 with the same families. |
| Problem list (frontend) | The list has one section per family, binary search first, each with its count. A unit test renders a 25-problem bank (`ResearchPage.test.tsx`). |

**Discrepancies found.**

1. **The demo does not label the 8 provisional problems as unreviewed.** The owner's decision of
   2026-10-25 07:50 says "the demo presents them as unreviewed". Neither `/problems`,
   `docs/demo.md` nor the landing page does so. Fixing this changes what users see, so I have
   **not** changed it; see action 2.
2. **The cloud container restarted twice during this work**, and Docker did not come back by
   itself. Each time the next sandbox step failed with "docker daemon unavailable". This
   stopped work but never produced a wrong result: those submissions stayed queued, or the
   evaluation exited with an error. The runs were repeated after a manual restart. This is an
   environment issue, not a repository one.

## 2. Status matrix

Each column is a separate claim. "Yes" means the evidence named in the legend exists for that
problem.

| Column | Evidence behind "yes" |
| --- | --- |
| Implemented | Statement, harness, reference, tests and error models committed |
| Content validated | `codeadapt-content validate` ok; content report committed |
| Sandbox validated | `test_demo_content` passed in CI run 112 under runc and gVisor. This checks that the measured `distinguishes` equal the declared ones, and that weak models equal documented limitations. |
| Error models evaluated | Every model's fingerprint was measured in the sandbox. The number is (models / models with a documented `known_limitation`). |
| Held-out synthetic | Author-written cases under v1.3, given as named right / named wrong / false alarms. "Named right" counts every case whose labelled model was named. |
| E2E pipeline | A submission ran through API, worker, sandbox, diagnosis, ledger and recommendation. **CI** = a sandbox e2e test in CI. **local** = `docs/demo/bank_check.py` against a dev API and worker on 2026-10-25 (a correct, a modelled and an unmodelled held-out program per problem, all matched: 39/39 new problems, 27/27 for first-true and the 8 provisional), not in CI. |
| Researcher workflow | **UI** = Playwright follows a submission of this problem to the trace and learner-model pages. **API** = the researcher trace and learner-model endpoints were read for this problem's submissions (`bank_check.py`). **list** = shown on `/problems` only. |
| Recommendable | `recommendable = true` |
| Real student code | Validated against programs not written by the project. **No problem has this.** |

| Problem | Family | Impl. | Content | Sandbox | Models (n / limited) | Held-out v1.3 | E2E pipeline | Researcher workflow | Rec. | Real code |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lower-bound | binary-search | yes | yes | yes | 8 / 1 | 6 / 0 / 0 (12 cases) | CI | UI, API | yes | no |
| count-occurrences | binary-search | yes | yes | yes | 4 / 1 | 2 / 0 / 0 (6) | CI | UI (student practice page), list | yes | no |
| last-less-than | binary-search | yes | yes | yes | 5 / 1 | 4 / 0 / 0 (7) | CI | list (researcher views not checked for it specifically) | yes | no |
| first-true | binary-search | yes | yes | yes | 9 / 1 | 2 / 0 / 0 (7) | local | API | no | no |
| integer-sqrt | binary-search | yes | yes | yes | 8 / 0 | 4 / 0 / 0 (8) | local | API, list | no | no |
| upper-bound | binary-search | yes | yes | yes | 7 / 0 | 3 / 0 / 0 (7) | local | API, list | no | no |
| exact-search | binary-search | yes | yes | yes | 6 / 0 | 3 / 0 / 0 (7) | local | API, list | no | no |
| last-occurrence | binary-search | yes | yes | yes | 6 / 1 | 3 / 0 / 0 (8; 1 predicted abstention) | local | API, list | no | no |
| min-capacity | binary-search | yes | yes | yes | 6 / 2 (ADR-032) | 4 / 0 / 0 (8) | CI (adaptation e2e), local | API, list | no | no |
| rotated-min | binary-search | yes | yes | yes | 5 / 1 | 4 / 0 / 0 (8) | local | API, list | no | no |
| rotated-search | binary-search | yes | yes | yes | 5 / 1 | 4 / 0 / 0 (8) | local | API, list | no | no |
| peak-index | binary-search | yes | yes | yes | 5 / 0 | 4 / 0 / 0 (8) | local | API, list | no | no |
| first-max-index | arrays | yes | yes | yes | 4 / 0 | 4 / 0 / 0 (8) | local | API, list | no | no |
| second-largest | arrays | yes | yes | yes | 4 / 0 | v1: 4 / **1** / 0; v2: 4 / 0 / 0 (8) | local | API, list | no | no |
| stock-profit | arrays | yes | yes | yes | 3 / 1 (non-unique) | 3 / 0 / 0 (7) | local | API, list | no | no |
| longest-run | arrays | yes | yes | yes | 4 / 0 | 4 / 0 / 0 (8) | local | API, list | no | no |
| plus-one | arrays | yes | yes | yes | 4 / 0 | 4 / 0 / 0 (8) | local | API, list | no | no |
| closest-pair-sum | two-pointers | yes | yes | yes | 4 / 0 | 4 / 0 / 0 (8) | local | API, list | no | no |
| container-water | two-pointers | yes | yes | yes | 4 / 1 (non-unique) | 4 / 0 / 0 (8) | local | API, list | no | no |
| dedup-sorted | two-pointers | yes | yes | yes | 4 / 1 (non-unique) | 4 / 0 / 0 (8) | local | API, list | no | no |
| max-window-sum | sliding-window | yes | yes | yes | 4 / 0 | 4 / 0 / 0 (8) | local | API, list | no | no |
| longest-sum-at-most | sliding-window | yes | yes | yes | 3 / 0 | 3 / 0 / 0 (7) | local | API, list | no | no |
| distinct-in-windows | sliding-window | yes | yes | yes | 3 / 0 | 3 / 0 / 0 (7) | local | API, list | no | no |
| pivot-index | prefix-sums | yes | yes | yes | 4 / 0 | 4 / 0 / 0 (8) | local | API, list | no | no |
| range-sum-queries | prefix-sums | yes | yes | yes | 3 / 0 | 3 / 0 / 0 (7) | local | API, list | no | no |

**Reading the held-out column.** No problem had a false alarm. Every unmodelled case in the
current versions abstained. The case counts are small (6–12 per problem), and the person who
wrote the models also wrote the cases. These numbers show that the method behaves as designed.
They do not show diagnostic accuracy.

- **second-largest.** The v2 result follows a test added after the first run. The case it fixes
  is no longer an independent check.
- **The original four problems.** Their numbers are from `docs/evaluation/adr030-2026-10-23`.
  Some of their modelled cases end in a time-limit symptom by design (ADR-027).

## 3. L21: what happens after a pass

### 3.1 Current behaviour

The pass branch is `PolicyV1.recommend` in `backend/src/codeadapt/adaptation/policy_v1.py`,
lines 166–203.

1. **Candidates.** The candidate set is built at lines 65–68:
   `family = [p for p in problems if p.family == spec.family and p.recommendable]`.
2. **Passed problems.** `passed` is every problem slug with a `no_failure_observed` attempt by
   this learner, and `remaining = [p for p in family if p.slug not in passed]`.
3. **When nothing remains.** If `remaining` is empty, the policy returns `Action.NONE` with no
   problem. Its rationale note is: "Every problem in the family has an attempt with no failure
   observed on its tests. That is not evidence of complete understanding."
4. **Otherwise.** The policy picks the least-evidenced remaining recommendable problem.

**Reproduction.** From `backend/`: `uv run python ../docs/reviews/2026-10-25/expansion-audit/l21_repro.py`. It calls the policy with the unit-test
fixtures.

| Learner history (all passes) | Action | Note |
| --- | --- | --- |
| first-max-index only | none | "Every problem in the family has an attempt with no failure observed…" |
| pivot-index only | none | same |
| lower-bound, count-occurrences, last-less-than, then integer-sqrt | none | same, although 9 binary-search problems were never attempted |
| integer-sqrt only | new problem: count-occurrences | — |

### 3.2 Where the wording goes wrong

The wrong claim appears in **two places**.

1. **The policy rationale**, `policy_v1.py` lines 179–180. It says "every problem in the
   family", but the code checked only the *recommendable* problems of the family. There is an
   empty family in two situations:
   - in every new family, because none of their problems is recommendable;
   - in binary search, once the three recommendable problems are passed, because the nine
     non-recommendable ones are never checked.

   This is stored in `recommendations.rationale` and shown on the researcher trace page.
2. **The student message**, `backend/src/codeadapt/api/recommendation.py` lines 35–39, for any
   `Action.NONE`. It reads: "Every problem in this family has an attempt of yours with no failing
   tests. There is nothing further to recommend here yet." After a single pass on first-max-index
   this is **false**: four other array problems are unattempted.

**L21 is wider than recorded.** The limitation as written covers only the new families. The
binary-search case (the third row of the table) also produces the false sentence. It has existed
since first-true became non-recommendable (policy 1.3, 2026-10-21), and it grew when the eight
provisional problems were added.

### 3.3 Can the wording be fixed without changing the policy?

**Yes.** The decision (action `none`, no problem, no criterion) depends only on `remaining`. The
sentence is a description of that decision, and a truthful description needs no new rule.
Example wordings:

- **Rationale:** "Every recommendable problem in the family has an attempt with no failure
  observed on its tests. That is not evidence of complete understanding."
- **Student:** "There is no further problem to recommend here yet. You can choose any problem from
  the list."

**This is still not a free change.**

- `tests/fixtures/policy_v1_golden.json` holds the current note 6 times. The golden test would
  need re-recording, and the diff would show that only the note changed.
- The note is stored per recommendation. Rows already stored keep the old wording, as the
  append-only tables require.
- Both sentences are claims shown to people, so they need your approval. I have **not** made
  this change.

### 3.4 Policy alternatives, if a pass should lead somewhere

None of these is implemented. Each one changes policy 1.4.

| Option | Behaviour | Trade-offs | Tests needed |
| --- | --- | --- | --- |
| **A. Wording only** (§3.3) | Unchanged | Honest; students still get no next step in the new families | Golden note diff only; an API test that `none` never claims all problems were passed |
| **B. Practice next in the same family, without a claim** | After a pass with no recommendable candidate, suggest the least-recently-attempted unpassed problem in the family, whether recommendable or not, with no target skill and no success criterion (`not_comparable`) | Gives a next step; but it lets non-recommendable problems be suggested, which reverses CE1 decision E2 for passes, and those problems' skill maps are unvalidated (L22) | Golden fixture regenerated with a diff review; binary-search recommendations for supported/ambiguous unchanged; no criterion recorded; follow-up evaluation stays `not_comparable` |
| **C. Cross-family step to a recommendable problem** | After a pass with no candidate in the family, recommend a recommendable problem from another family (today only binary search) | Always has a candidate; but it links unrelated skills and would send an array learner to binary search, which is a pedagogical claim nobody has tested | Ranking tests across families; check that no skill target or criterion crosses families; golden diff |
| **D. Make some new-family problems recommendable** | Unchanged policy; a candidate exists | Needs the existing criteria (validation of the problem and its skill map), which no new problem meets today (L22) | The CE1 regression set for each problem made recommendable |

**Recommendation:** A now, which needs your approval of the wording. Decide B, C or D later,
after real-learner data.

## 4. L22: the five new skill keys

**How evidence arises (unchanged rules).**

- **`incorrect`.** A named, unqualified diagnosis gives an `incorrect` observation to its model's
  skill.
- **`correct`.** Rule C gives a `correct` observation to every skill whose probing tests all
  passed.
- **Counting.** Only the first reliably evaluated attempt per problem version is counted
  (LM1).
- **Pooling.** Observations are pooled by key across every problem and family.

**The mapping.** For each problem, the cell gives the error models mapped to the skill and, in
brackets, the number of tests that probe it. `*` marks a documented collision (ADR-032 route):
that model gives no `incorrect` evidence.

| Skill | arrays | two-pointers | sliding-window | prefix-sums |
| --- | --- | --- | --- | --- |
| `index_range` | first-max-index: skips_last (7); second-largest: skips_first (7); stock-profit: misses_last_day (6); plus-one: adds_at_front (7) | closest-pair-sum: allows_same_element, skips_first (6); container-water: width_plus_one, stops_before_adjacent (8); dedup-sorted: skips_last (6) | max-window-sum: misses_last_window (6); longest-sum-at-most: length_without_plus_one (5); distinct-in-windows: misses_last_window (6) | pivot-index: **none** (8); range-sum-queries: excludes_right_end (8) |
| `update_rule` | second-largest: no_demotion (7); longest-run: last_run_unchecked, compares_to_first (11); plus-one: single_carry, carry_never_cleared (8) | closest-pair-sum: moves_wrong_pointer (7); container-water: moves_taller* (8); dedup-sorted: compares_to_first, counts_without_writing (7) | max-window-sum: never_subtracts, subtracts_wrong_element (11); longest-sum-at-most: restarts_window (10); distinct-in-windows: keeps_zero_counts (8) | pivot-index: pivot_counted_left, pivot_counted_right (12); range-sum-queries: prefix_not_accumulated (9) |
| `output_contract` | first-max-index: returns_value (4); second-largest: zero_when_none (3); stock-profit: ignores_order*, allows_loss (9); longest-run: returns_value (5); plus-one: no_new_digit (3) | closest-pair-sum: signed_gap (4); container-water: uses_taller_height (5); dedup-sorted: returns_last_index* (5) | longest-sum-at-most: strict_limit (7) | pivot-index: size_when_none (3); range-sum-queries: ignores_left_end (5) |
| `tie_resolution` | first-max-index: last_of_ties (7); second-largest: counts_duplicates (7) | — | distinct-in-windows: counts_unique_only (6) | pivot-index: last_pivot (4) |
| `accumulator_init` | first-max-index: max_starts_at_zero (7); longest-run: reset_to_zero (6) | — | max-window-sum: best_starts_zero (4) | — |

**Why treat these as one skill.** Each key names one observable kind of mistake that shows up
the same way across problems:

- **`index_range`:** the loop visits the wrong set of positions.
- **`update_rule`:** some piece of tracked state is not updated.
- **`output_contract`:** the right computation is returned in the wrong form.
- **`tie_resolution`:** equal values are handled against the specification.
- **`accumulator_init`:** a running value starts at the wrong value.

This is the definition rationale recorded in ADR-033, and it is an **assumption**.

**Confounds and cross-family differences.**

1. **`update_rule` is the broadest key.** It joins very different mechanisms:
   - carry propagation (plus-one);
   - pointer choice (closest-pair-sum, container-water);
   - removing the leaving element (max-window-sum, distinct-in-windows);
   - shrinking versus restarting (longest-sum-at-most);
   - prefix accumulation (range-sum-queries);
   - demoting the old maximum (second-largest);
   - closing the final run (longest-run).

   A learner who gets carries right has shown nothing about window removal. Pooling them
   inflates or deflates one estimate with unrelated evidence.
2. **`index_range` mixes several errors:**
   - end-of-loop off-by-one (most models);
   - direction (`adds_at_front`);
   - pairing an element with itself (`allows_same_element`);
   - measuring a window (`length_without_plus_one`).

   The last two are arguably different misconceptions.
3. **`tie_resolution` mixes two questions.** One is "which equal candidate wins" (first-max-index,
   pivot-index). The other is "do duplicates count separately" (second-largest,
   distinct-in-windows). `counts_unique_only` is arguably a misreading of "distinct".
4. **Evidence that can only be positive.** pivot-index declares `index_range` and has 8 probing
   tests, but no `index_range` model. It can only ever give `correct` observations for that
   skill, through rule C (L19).
5. **Unequal opportunity.** Each attempt gives at most one observation per skill, whatever the
   number of probing tests. Some problems probe `output_contract` with only 3 tests:
   second-largest, plus-one, pivot-index. On those problems, rule C gives `correct` even to
   programs that never reach the contract-relevant case.
6. **Family imbalance.** `accumulator_init` and `tie_resolution` have no two-pointer problems.
   The learner model will cross its display threshold (3 observations from 2 problems) using
   arrays alone for some keys.
7. **Skills are decided by assumption.** A program that fails because of a misread specification
   can match an `update_rule` model. Three such cross-skill equivalences were found and
   neutralised, but the search was not exhaustive (L20).

**What synthetic tests can check, and what needs real learners.**

| Question | Synthetic tests (possible now) | Needs real learner data |
| --- | --- | --- |
| Each skill's evidence comes only from its own models, and qualified models give none | Yes, already unit-tested (`test_bank_expansion.py`) | — |
| No two models under different keys are output-identical (non-unique attribution) | Partly: alternative-cause search on random inputs. It found 3 cases; it is not exhaustive | Real programs show which alternative causes actually occur |
| Every declared skill can receive `incorrect` evidence somewhere | Yes: a static check (it would flag pivot-index `index_range`) | — |
| Errors under one key co-occur in the same learner across families (the pooling assumption) | No | Yes: per-learner error patterns across problems |
| A key's evidence predicts later performance on other problems with that key | No | Yes: longitudinal attempts, and fitted rather than assumed BKT parameters |
| The keys are understandable to teachers or researchers | No | Expert review |

**No mapping is changed here.** Splitting a key (for example `update_rule` into state update
versus pointer or window movement), or adding models, would need your approval.

## 5. The eight provisional binary-search problems

The eight are integer-sqrt (CE1.2), min-capacity (CE1.3), upper-bound, exact-search,
last-occurrence, rotated-min, rotated-search and peak-index. They are provisional under your
decision of 2026-10-25 07:50.

### 5.1 Checks run for this audit

**Reference correctness** (`expansion-audit/bsx_check.py <slug> 600`). Native build; 600 random inputs per
problem; each reference was compared with an independent Python brute force. Small arrays were
used, with duplicates where the contract allows them; integer-sqrt also used the full range up
to 2^31 − 1.

- All 4,800 comparisons agree. **No reference defect was found.**
- No two error models of a problem were output-identical on the random inputs.

**Plausible programs outside the models.** These were compiled against each harness and run on
the committed tests.

| Program | Result on the tests | What the system would record |
| --- | --- | --- |
| Linear scan: upper-bound, exact-search, last-occurrence, rotated-min, rotated-search, peak-index | **Passes every test** on all six problems, with the slowest test at 0.016 s | Through the pipeline (upper-bound): `no_failure_observed`, "all tests passed", and a new-problem recommendation. Rule C gives `correct` observations to every probed skill. |
| `std::upper_bound` call (upper-bound) | Passes every test | Through the pipeline: the same as the linear scan, although the statement forbids the call |
| `std::sqrt` on a `double` (integer-sqrt) | Passes every test | Correct: the result is exact for 32-bit inputs |
| Linear capacity search (min-capacity) | Fails one test (`large_one_day`) by time limit | Through the pipeline: `non_termination_observed`, a retry, and no skill named (ADR-027) |
| `int` product `mid * mid` (integer-sqrt) | Fails 7 tests, with outputs depending on overflow, and 1 by time limit | Through the pipeline: `unreliable_evidence` (the sanitizer build flags the overflow). The student gets the inconsistent-behaviour message, a retry, and no skill evidence. This is safe. |

### 5.2 Confirmed defects

These are reproducible with the commands above.

**D1. Complexity and banned library calls are not enforced, yet they still give skill
evidence.** Six of the eight statements say "O(log n)", and three say "do not call
`std::upper_bound`". A linear scan or a banned call passes every test. Rule C then gives it
`correct` observations for skills such as `search_space_boundaries` and `loop_termination`.

The non-assessment of complexity is documented (component-interfaces §5, and the 2026-10-21
critical review found it for the original problems). But the statements promise a requirement
the system does not check. This is a defect of the **content–system contract**, not of the
references.

Fixing it is an evidence-policy or content decision. The options are:

- larger tests with a tight time limit;
- a static check for banned calls;
- no rule C evidence on problems whose central technique is not verified.

Each option needs your approval.

### 5.3 Design questions (not defects)

**Q1. Mapping choices that are debatable.**

- **last-occurrence `missing_equality_check`** is mapped to `problem_specification`. Its name
  suggests `equality_handling`. It is single-group and qualified, so it gives no evidence
  either way today.
- **integer-sqrt `hi_excludes_x` and `hi_cap_46340`** are mapped to `search_space_boundaries`.
  They differ from the reference on 1 of 600 and 0 of 600 random inputs, and only 2 tests
  each detect them. They are hard to reach and give little evidence. This is a coverage
  question, not an error.
- The min-capacity and rotated-min mappings are covered in `skill-mapping-review.md`. ADR-032
  is unchanged.

**Q2. Integer overflow is unmodelled** (integer-sqrt design record, U1). The table above shows
what such a program receives. Whether overflow needs its own model or skill is a taxonomy
question for you.

**Q3. Search for cross-skill equivalences.** No alternative-cause search (the L20 method) was run
on upper-bound, exact-search, last-occurrence, rotated-search, peak-index or integer-sqrt. Only
min-capacity and rotated-min were reviewed. Until it is run, any of their named diagnoses could
carry a non-unique attribution.

### 5.4 Missing evidence

- **No independent or real-student programs** for any of the eight problems.
- **No calibration set, and no written regression comparison**, for integer-sqrt and
  min-capacity. The CE1.2 authorisation required both, and the gap is already recorded in
  `ce1-status.md`.
- **Pipeline coverage.** `bank_check.py --slugs ...` was run locally against a dev API and worker
  for first-true and the eight problems: 27 of 27 held-out programs matched their labels (pass;
  labelled model named; abstention). In CI only min-capacity goes through the pipeline (adaptation
  e2e); the others are covered by `test_demo_content` and the held-out evaluation shard.

**No problem here is marked research-validated**, and none should be on synthetic evidence.

## 6. Recommended actions, in priority order

| # | Action | Needs your approval? |
| --- | --- | --- |
| 1 | Correct the L21 sentences (§3.3, option A) in the rationale and the student message, re-record the golden note, and keep stored rows unchanged | **Yes**: user-facing wording and the policy golden output |
| 2 | Label the 8 provisional problems as "unreviewed" on `/problems` and in `docs/demo.md`, as your 07:50 decision describes | **Yes**: user-facing; no content-version change if done in the UI only |
| 3 | Decide D1: how statements that ban techniques or require O(log n) should relate to skill evidence | **Yes**: evidence policy or content |
| 4 | Run the alternative-cause search (L20 method) on the six unsearched provisional problems; document any equivalence through the existing ADR-032 route only after you approve each one | The search: no. Any new `known_limitation`: **yes** |
| 5 | Add a static check, as a test, that every declared skill has at least one model. It currently fails for pivot-index `index_range`, so decide first whether to add a model or drop the declaration | **Yes** for the content change; the check itself is test-only |
| 6 | Move `bank_check.py` coverage into CI, for example one sandbox e2e test per family, so the 13 new problems have CI end-to-end coverage | No (test-only), but it lengthens CI (L16) |
| 7 | Review the integer-sqrt and min-capacity gate submissions (CE1.2, CE1.3) and the six BSX problems for acceptance | **Yes** (pending since 07:50) |
| 8 | L22: decide whether to split `update_rule` and `index_range` before any new-family problem becomes recommendable | **Yes** |
| 9 | Plan real-learner or independent-program validation (VAL1-B or PC1), the only route to research validation | **Yes** |
