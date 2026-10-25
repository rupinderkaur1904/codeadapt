# Proposal: milestone CE1, content expansion and validation (for owner review)

Status: **proposed, not started** (2026-10-17). This was written from the repository at
`ab1259c`. Nothing here changes diagnosis, feedback, the recommendation policy or the
learner model's visibility.

## 1. Audit of the current bank

Sources:
- `content/demo/*/problem.toml`;
- the measured reports in `docs/content-reports/`;
- `eval/heldout`, `eval/calibration`;
- `docs/content-design/`.

### 1.1 Problems, models and coverage

| Problem | Tests (samples) | Error models | Held-out cases | Design record |
| --- | --- | --- | --- | --- |
| lower-bound | 17 (2) | 8 | 7 (+5 calibration) | yes (`lower-bound.md`) |
| count-occurrences | 15 (2) | 4 | 5 | **no** |
| last-less-than | 15 (2) | 5 | 5 | **no** |

All three problems are in one family (`binary-search`) and share the same four skills:
- `search_space_boundaries`;
- `loop_termination`;
- `equality_handling`;
- `problem_specification`.

Measured behaviour-group support for each model (from the reports):

| Skill | Models that can give an `incorrect` observation (unqualified) | Models that never can |
| --- | --- | --- |
| equality_handling | `upper_bound_confusion` (6 groups), `stops_at_first_match` (3) in lower-bound; `upper_uses_strict` (2) in count-occurrences; `uses_le` (2) in last-less-than | — |
| problem_specification | `exact_match_sentinel` (7), `returns_wrong_pointer` (11) in lower-bound; `inclusive_count` (4) in count-occurrences; `returns_insertion_point` (5), `clamps_to_zero` (2) in last-less-than | — |
| loop_termination | `no_progress_update` in all three (6/3/3 groups); `closed_loop_hi_mid` (9) in lower-bound | — |
| search_space_boundaries | **only `hi_skips_candidate` (3 groups) in lower-bound** | `hi_init_last_index` in all three problems (1 group, documented collision) |

### 1.2 Gaps, in priority order

1. **Boundary errors are observable in one problem only.** A failure on
   `search_space_boundaries` can become skill evidence only through `hi_skips_candidate`
   in lower-bound. In the other two problems the only boundary model is a documented
   collision, so it never adds failure evidence (policy 1.2). The learner model therefore
   sees boundary failures from at most one problem.
2. **No prerequisite problem (gap G1).** A learner who struggles has nowhere simpler to
   go, and the curriculum's `prerequisites` links all point at lower-bound.
3. **No transfer problem (gap G3).** Every observation comes from the same problem shape:
   a sorted array plus a target. Passing all three says nothing about whether the skill
   carries to a new context.
4. **Termination evidence is only time limits (gap G2).** Every `loop_termination` model
   is detected only by `time_limit` signatures. After ADR-023 these are CPU-limit stops, but
   a time limit is still the least specific signature: any slow program produces one.
   There is no exercise in which a terminating but wrong update is visible in the output.
5. **Validation debt on existing content.**
   - count-occurrences and last-less-than have no design records.
   - 8 of the 17 model instances have no held-out case: in lower-bound
     `no_progress_update`, `stops_at_first_match`, `hi_skips_candidate`,
     `closed_loop_hi_mid` and `returns_wrong_pointer`; in count-occurrences
     `no_progress_update`; in last-less-than `hi_init_last_index` and
     `no_progress_update`. The proposal first said "5 of 17", counting by model name
     within lower-bound only; this was corrected in CE1.0.
6. **One family, and skills defined only in binary-search terms.** The learner model's
   "distinct problems" threshold is met entirely inside one family. This is CE2's job,
   not CE1's, but it limits what any estimate can mean.

### 1.3 Follow-up relationships today

- Lower-bound lists the other two as equivalents.
- Both of them list lower-bound as their prerequisite and each other as equivalents.
- There are no transfer links.
- Policy v1 recommends within the family, by skill-probe density. After all three are
  attempted it falls back to a retry or to "none".

### 1.4 Does the bank support the learner model?

**Not yet in a meaningful way.**
- **Observation ceiling.** With one counted attempt per problem version, a learner has at
  most 3 counted observations per skill.
- **Search-space boundaries.** At most one of those 3 observations can be `incorrect`.
- **What a `correct` observation is.** It comes from a whole set of tests passing, which is
  weak evidence.

Sensitivity of the estimates to the assumed parameters
(`docs/evaluation/bkt-sensitivity-2026-10-17/`) is large on sequences this short:
- For "one incorrect, then two correct" the assumed set gives P(known) 0.831. Across an
  81-point grid around it (P(L0) 0.1–0.5, P(T) 0.05–0.2, P(G) 0.1–0.3, P(S) 0.05–0.2) the
  range is 0.468 to 0.982.
- For "correct, correct, incorrect" the range is 0.140 to 0.966.
- Varying one parameter at a time, P(G) and P(T) matter most and P(S) least.

So the displayed number is driven mostly by the assumptions. Content expansion raises the
observation ceiling, but only real-learner data can fix the parameters. This is a technical
sensitivity check, not validation.

## 2. Proposed CE1 scope: complete the binary-search family

CE1 has five stages, run strictly one at a time. Each stage must pass its gate before the
next starts. The order puts validation debt first and then targets the gaps above in
priority order.

| Stage | Content | Gap addressed |
| --- | --- | --- |
| CE1.0 | Design records for count-occurrences and last-less-than. Held-out cases for the 8 model instances without one, written before running the method. No content-version change unless a record proposes one. | 5 |
| CE1.1 | **G1, "first true"**: return the first index of a monotone boolean array (a partition point). It isolates boundaries and termination from equality handling. Target: at least two boundary models with ≥ 2 behaviour groups each, so boundary failures become observable outside lower-bound. | 1, 2 |
| CE1.2 | **G2, "integer square root"** (floor √x for 0 ≤ x ≤ 2³¹−1, using 64-bit arithmetic): a search over an answer range in which a wrong but terminating update gives a wrong output, not only a time limit. Signed-overflow variants are undefined behaviour, so they are not modelled; they are recorded as unmodelled. | 4, 1 |
| CE1.3 | **G3, "minimum feasible capacity"**: the smallest capacity that ships ordered packages within D days. It is a search over the answer space with a feasibility check, transferring all four skills to a new context. | 3 |
| CE1.4 | Family report: re-run the observation-capacity table (§1.4) and the sensitivity script on the six-problem bank. Update the curriculum links: G1 as prerequisite, G3 as transfer. | 1–3 |

New problems reuse the four existing skills. A new skill is added only if a design record
shows a modelled error that none of them describes; that would be a separate decision for
you.

### Acceptance criteria for each new problem (CE1.1–CE1.3)

1. **Design record first.** A record in `docs/content-design/<slug>.md` with the seven
   sections of the content method (objective, plausible errors, test audit, matrix,
   evidence-to-concept mapping, follow-ups, limitations) is written before the content is
   final.
2. **Executable bug models.**
   - At least one model per targeted skill, and every model executable and deterministic.
   - Every model is separated from the reference and pairwise from every other model.
   - Every model is supported by ≥ 2 behaviour groups, or its weakness is documented as
     `known_limitation`.
3. **Measured, not declared.**
   - `codeadapt-content validate` passes.
   - Every declared `distinguishes` agrees with the measured matrix.
   - The report is generated into `docs/content-reports/` and regenerates identically.
4. **Ambiguity analysis.** Collisions with plausible unmodelled errors are analysed in the
   record. Any that cannot be separated are kept as documented limitations, never forced
   into a pick.
5. **Held-out evaluation.**
   - At least 4 held-out cases (at least one correct, one unmodelled), committed before the
     method is run on them, in a different style from the models.
   - Results are reported with raw counts and never pooled with calibration cases.
6. **Connected follow-ups.**
   - `[curriculum]` links (prerequisites, equivalents, transfer) are set.
   - The record states which follow-up each diagnosis outcome should lead to.
   - Policy v1 is not changed to act on them (see decision E2).
7. **No regression.**
   - Existing problems keep their content versions.
   - `codeadapt-eval` held-out and calibration results for them are byte-identical before
     and after.
   - Full suite and CI green.
8. **Learner-model check.** The observation-capacity table and the sensitivity script are
   re-run and reported as technical results, labelled as such.

### Not in CE1
- No change to student-facing diagnosis or feedback policy (v1.1).
- No change to the recommendation policy except as decided in E2.
- No BKT estimate shown to students or used for recommendations.
- No parameter fitting.
- No new families: arrays, strings and the rest are CE2–CE5, as in
  `docs/content-design/README.md` §2.

## 3. Decisions for the owner

| ID | Question | Recommendation |
| --- | --- | --- |
| E1 | Approve the CE1 scope and stage order above (CE1.0 → CE1.4, each gated) | approve |
| E2 | Policy v1 picks the next problem from the whole family, so adding G1–G3 to `binary-search` would change which problems it recommends, without any policy code change. Should new problems (a) be recommendable by v1 as they are, or (b) be excluded from v1's candidate set until a separate policy decision on prerequisite step-back and transfer? | **(b)**. Recommendations stay exactly as today; the new problems are still in the problem list, and their attempts still feed skill evidence and the researcher-only learner model. This needs a small, tested filter in v1 (a `recommendable` flag on content), which I would document as policy 1.3 with no change to its rules. |
| E3 | Problem choices G1 "first true", G2 "integer square root", G3 "minimum feasible capacity" | approve, or name replacements |

## 4. Risks
- Problems I design and evaluate with my own held-out cases are not independent tests.
  Independently written cases, from someone other than the model author, remain the main
  validation gap.
- A G3 transfer problem can show that a skill's observations exist in a new context. It
  cannot show that learning transfers.
- More observations per skill reduce, but do not remove, the estimates' dependence on the
  assumed parameters.
- Every new problem adds fingerprint measurement time in CI: about 95 s locally for
  lower-bound.
