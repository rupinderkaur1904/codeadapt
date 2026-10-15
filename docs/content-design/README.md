# Content design method

How CodeAdapt problems are designed. Every problem is a measuring instrument first and an
exercise second. Its tests, bug models and follow-ups are designed together, backwards from
what it should let the system conclude. The worked example is
[lower-bound.md](lower-bound.md).

## 1. Design record for every problem

Each problem gets a record in this folder, written **before** the content is finalised.
It covers:

1. **Learning objective.** The concept, the subskills (skill keys), the assumed
   prerequisites, and what is deliberately not assessed.
2. **Plausible errors.** For each one: whether it can be modelled. An error cannot be a
   model if it is undetectable, has undefined behaviour, or is outside the single-error
   space.
3. **Test audit.** For each test: the behaviour exercised, the expected output, the
   models it *measurably* separates from the reference, its skills, why it is not
   redundant, and its multi-cause risk.
4. **Discrimination matrix.** Measured with `codeadapt-content validate`, never written
   by hand. It covers separation from the reference, pairwise separation, behaviour groups
   (tests every model passes or fails together), collisions, and errors the suite cannot
   see.
5. **Evidence-to-concept mapping.** For each observed pattern: the candidate hypotheses,
   the skill, the strength of evidence (counted in behaviour groups, not tests), the
   limitation, and the next activity.
6. **Follow-up and curriculum links.** Prerequisites, equivalent practice, transfer
   problems, which earlier skills the problem reassesses, and the gaps.
7. **Proposed changes and known limitations.**

Rules that apply throughout:

* A failing test is evidence of a behavioural difference, not of a misconception. A
  failure that no diagnosis explains is not evidence about a skill.
* If two errors cannot be separated, either add a test that separates them or keep the
  ambiguity on purpose. Never force a pick.
* Add tests for diagnostic value, not volume: each test either separates something or
  has a stated reason to exist (minimal case, scale, sample).
* *Calibration* cases (written while designing, used to tune tests) are kept apart from
  *held-out* cases (written before the method is run on them, used only for reporting).
  Calibration cases go in `eval/calibration/`; held-out cases in `eval/heldout/`.
* Synthetic results are reported with their counts and limitations, never as evidence of
  real-student accuracy or learning.

## 2. Milestone CE: content expansion

CE runs after M7 and alongside M8. M8 is the deployment gate; CE changes no isolation
code. CE is delivered in stages, each ending with validation, evaluation and the full
regression suite.

| Stage | Scope | Acceptance |
| --- | --- | --- |
| CE0 | Method and tooling: this document and the lower-bound record. `problem.toml` gains per-test `purpose` and `distinguishes`, plus `[curriculum]` links (prerequisites, equivalents, transfer). Validation checks each declared `distinguishes` against the measured matrix. `codeadapt-content report` writes the matrix, behaviour groups and collision list to `docs/content-reports/<slug>.md`. `eval/calibration/` is created. | Declared and measured discrimination agree for all three existing problems. Reports regenerate byte-identically. Existing held-out results are unchanged. |
| CE1 | Binary-search family redesigned and completed: apply lower-bound changes C1–C2, write records for count-occurrences and last-less-than, add prerequisite G1, termination exercise G2, and one transfer problem G3. | Every model is supported by at least 2 behaviour groups, or its weakness is documented and preserved. Each new problem has at least 4 held-out cases (at least one correct, one unmodelled) written before evaluation. Metrics are reported with counts. |
| CE2 | Arrays and two pointers / sliding window (4–5 problems, including one prerequisite and one transfer) | As CE1, plus at least one skill shared with binary search (e.g. `search_space_boundaries` as an interval-boundary skill), so a concept appears in more than one context. |
| CE3 | Strings and hashing; stacks and queues (5–6 problems) | As CE2 |
| CE4 | Recursion, linked lists, trees (5–6 problems). The harnesses build the structures; students never see the harness source. | As CE2, plus a harness review for hidden-data leaks |
| CE5 | Sorting and basic graph traversal (BFS/DFS) (4–5 problems) | As CE2. Total bank 20–30 problems |

Across all stages:

* No new execution path. Everything runs through the existing sandbox, evidence and
  diagnosis code.
* Adding a problem must not change any existing problem's content version unless a design
  record proposes it. The regression check compares `codeadapt-eval` results for
  unchanged problems before and after, byte for byte.
* Policy changes needed by the curriculum (prerequisite step-back, purpose-built
  discriminating exercises, ledger change C5) are separate ADRs with their own synthetic
  trajectories. They are not side effects of adding content.
