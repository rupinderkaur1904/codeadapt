# L20 safeguard S1 for the original problems: cases O1–O4 (2026-10-26)

**Status.** Applied (owner request 2026-10-26 05:22; ADR-037).

**Scope.** The four clear-cut cross-skill twins found by
[l20-search-original.md](l20-search-original.md) §2.1 now carry a `known_limitation`. The
four contestable cases (O5–O8) and the two unsupported ones (O9–O10) are **not changed**
(§6 below).

**Process.** This is the process of ADR-032 and ADR-036:

- one `known_limitation` per model, naming the twin and the case;
- a new content version per problem;
- fingerprints, behaviour groups, mappings, diagnosis method, rule C, recommendation policy
  and BKT parameters are unchanged.

The classifications are mine and no second reviewer has checked them. Nothing here measures
diagnostic accuracy.

## 1. Evidence check

Before changing anything I re-read the committed raw output
(`l20-search-original/results.txt`) and the four alternative programs. For each pair:

- the output differs on **0** committed tests;
- it differs on **0 / 1 260** exhaustive inputs (first-true: **0 / 91**);
- it differs on **0 / 3 000** random inputs (seed 20261026);
- a one-line argument, given below, makes the equivalence exact on the whole valid domain.

The model's own measured fingerprint (docs/content-reports/) has 2 or more behaviour groups,
so before this change v1.3 named each one **unqualified** and it gave an `incorrect`
observation.

| Case | Model | Behaviour groups | Detecting tests |
| --- | --- | --- | --- |
| O1 | lower-bound `upper_bound_confusion` | 6 | 8 |
| O2 | last-less-than `uses_le` | 2 | 7 |
| O3 | last-less-than `clamps_to_zero` | 2 | 6 |
| O4 | first-true `none_sentinel` | 2 | 5 |

## 2. O1: lower-bound `upper_bound_confusion`

**What the problem requires.** "Return the smallest index `i` such that `a[i] >= target`. If
no such index exists, return `a.size()`." That is the lower bound.

**The model** (skill `equality_handling`). It is a half-open search that tests
`a[mid] <= target` where `<` is needed. It returns the first index with `a[i] > target`,
which is the upper bound.

**The alternative.** `l20-search-original/lower-bound/first_gt_by_spec.cpp` reads the task
as "first element greater than the target", and is a correct closed-interval search for that
reading, with an answer variable. Its cause is `problem_specification`.

**Why the match is clear-cut.** Both are correct implementations of the same function, the
upper bound, so they agree on every valid input. Misreading `>=` as `>` is a plausible,
distinct cause: the four sibling problems ask for exactly these nearby boundaries. It is the
`equality_handling` analogue of the S1 cases #1 and #7 (ADR-036).

**Is the qualification appropriate?** Yes.

- The student hint, "Check which side of the boundary elements equal to the target end up
  on", is sound advice for both causes.
- The feedback now adds "other mistakes can produce the same pattern… one possible cause to
  check".
- `equality_handling` keeps negative evidence in lower-bound through `stops_at_first_match`.
  O8 is contestable and unchanged, so that model still gives `incorrect` observations.

## 3. O2: last-less-than `uses_le`

**What the problem requires.** "Return the largest index `i` such that `a[i] < target`. If
no such index exists, return `-1`."

**The model** (skill `equality_handling`). It uses `a[mid] <= target` where `<` is needed
and returns `lo - 1`, which is the last index with `a[i] <= target`, or −1.

**The alternative.** `last-less-than/last_le_by_spec.cpp` reads the task as "last element
≤ target" and is a correct search for that reading. Its cause is `problem_specification`.

**Why the match is clear-cut.** Both compute upper bound − 1, the last index with
`a[i] <= target` (−1 when none). The argument and the misreading are those of O1.

**Is the qualification appropriate?** Yes.

- The hint, "Check whether an element equal to the target should count as less than it", is
  sound advice for both causes.
- **Consequence:** `uses_le` is the only `equality_handling` model in last-less-than, so that
  skill becomes **positive-only** there. Its `positive_only_skills` reason says so, as the
  content check requires.

## 4. O3: last-less-than `clamps_to_zero`

**What the problem requires.** As in O2: when no element is less than the target, return −1.

**The model** (skill `problem_specification`). It is a correct search that returns
`lo > 0 ? lo - 1 : 0`, so an absent answer becomes 0.

**The alternative.** `last-less-than/answer_starts_zero.cpp` is a correct closed-interval
search whose answer variable starts at 0 instead of −1. The answer −1 is unreachable. Its
cause is `search_space_boundaries`, the classification used for S1 case #4 (ADR-036).

**Why the match is clear-cut.** The answer variable records the last `mid` with
`a[mid] < target`, which is lower bound − 1 whenever that exists. Otherwise it keeps its
initial 0. Both programs therefore return max(lower bound − 1, 0) on every valid input.

**Is the qualification appropriate?** Yes.

- The hint, "Re-read what should be returned when no element is less than the target", fits
  both causes.
- `problem_specification` keeps negative evidence in last-less-than through
  `returns_insertion_point`. O6 is contestable and unchanged.

## 5. O4: first-true `none_sentinel`

**What the problem requires.** "Return the index of the first 1. If there is no 1, return
`flags.size()`."

**The model** (skill `problem_specification`). It is a correct search that returns −1
instead of `flags.size()` when there is no 1.

**The alternative.** `first-true/answer_var_starts_minus_one.cpp` searches [0, n − 1] with
an answer variable that starts at −1, so the answer n is unreachable. Its cause is
`search_space_boundaries`, the same classification as S1 case #4.

**Why the match is clear-cut.** The answer variable ends at the first 1 if there is one and
at −1 otherwise. That is exactly the model's output.

**Is the qualification appropriate?** Yes.

- The hint, "Re-read what the function must return when the array contains no 1", fits both
  causes.
- `problem_specification` keeps negative evidence in first-true through
  `returns_last_false` and `returns_any_true`. O7 is contestable and unchanged.
- first-true is not recommendable (E2), and this change does not touch that flag.

## 6. Cases left unchanged

Neither group is changed. Each still gives `incorrect` evidence when named unqualified, and
`test_the_contestable_cases_are_not_changed` in backend/tests/unit/test_l20_safeguards.py
pins this.

### Contestable: O5–O8

| Case | Model | Recommendation | Rationale |
| --- | --- | --- | --- |
| O5 | lower-bound `returns_wrong_pointer` | Keep | The alternative returns the wrong end of the final interval. The bank maps that cause to `problem_specification`, the model's own skill, so the twin is same-skill under the bank's mapping. This is the general question of l20-contestable-cases.md decision 1. |
| O6 | last-less-than `returns_insertion_point` | Keep | The alternative records `mid + 1`. It is the same kind of case as #13, where the recommendation is to keep: no declared skill fits the alternative better. |
| O7 | first-true `returns_last_false` | Keep | A closed loop that returns `hi`, the same as case #3. The recommendation follows that one. |
| O8 | lower-bound `stops_at_first_match` | Keep | Only the half-open program that shares the model's exact loop is a twin. The natural closed-interval program for the same reading differs on 3 tests, 194 exhaustive and 97 random inputs. The reading ("any copy, else the insertion point") is compound and less plausible than the single misreadings above. |

**What would change O5–O7.** An owner decision that "which variable to return or record at
the end" is not a `problem_specification` error. That decision should be taken once, for
every model of that kind:

- lower-bound `returns_wrong_pointer`;
- upper-bound `returns_last_not_greater`;
- first-true `returns_last_false`;
- integer-sqrt `returns_lo_closed`;
- last-less-than `returns_insertion_point`.

### Unsupported: O9–O10

| Case | Model | Recommendation | Rationale |
| --- | --- | --- | --- |
| O9 | first-true `lo_init_one` | Keep | The equivalent program replaces a result of 0 by 1 after a correct search. No reading of the task produces it, so it is not a plausible cause. |
| O10 | first-true `hi_skips_candidate` | Keep | The equivalent program's extra guard is a no-op. It still discards the candidate with `hi = mid - 1`, so its cause is the model's own cause. |

## 7. Changed files and versions

**Content versions** (earlier versions stay registered with their own snapshots, ADR-023
D4):

| Problem | Before (f752a51) | After |
| --- | --- | --- |
| lower-bound | `9aade9e1396e…` | `8ca53699ef0d…` |
| last-less-than | `4208517a8d24…` | `ecdcad684935…` |
| first-true | `485c974b4928…` | `c5285489e34a…` |

**Content changes.**

- `content/demo/lower-bound/problem.toml`, `content/demo/last-less-than/problem.toml`,
  `content/demo/first-true/problem.toml`: one `known_limitation` per model.
- `content/demo/last-less-than/problem.toml` also gains a `positive_only_skills` reason for
  `equality_handling`.

**Tests.**

- `backend/tests/unit/test_l20_safeguards.py`: the O1–O4 cases, run through every S1 check:
  - the limitation is recorded and the mapping kept;
  - no negative evidence;
  - rule C unchanged;
  - no BKT update;
  - qualified feedback;
  - the recommendation is unchanged and marked qualified.

  It also covers O5–O10 as unchanged, and an old lower-bound snapshot that keeps its
  evidence.
- `backend/tests/unit/test_adaptation.py`: the golden policy fixture is kept as policy 1.2
  produced it. The test now applies exactly this change, two rationale fields in 12 of 286
  entries, and requires everything else to be identical.
- **Fixtures moved to `stops_at_first_match`.** Several tests used `upper_bound_confusion` as
  their example of an unqualified diagnosis, and now use `stops_at_first_match`. Each has a
  comment saying why. The files are:
  - `test_adaptation.py` (`LB_EQUALITY`);
  - `test_feedback.py`;
  - `test_skill_evidence.py`;
  - `test_technique_eligibility.py`;
  - `test_trajectories.py`;
  - `tests/sandbox/test_adaptation_end_to_end.py`.

  The tests' expectations about evidence are unchanged.
- `backend/tests/unit/test_min_capacity_attribution.py`: the documented collisions of the
  three problems.
- `backend/tests/sandbox/test_demo_content.py`: `NON_UNIQUE_ATTRIBUTION` lists the four
  models.
- `backend/tests/sandbox/test_family_end_to_end.py`: the binary-search family's named case
  was last-less-than `closed_interval_le.cpp` (`uses_le`). That file is now a qualified case,
  and `returns_count_below.cpp` (`returns_insertion_point`) is the named case. The full
  sandbox run caught this as the one failure, and the rerun passes.

**Docs.**

- docs/decisions.md ADR-037.
- docs/limitations.md L20.
- The design records of the three problems.
- l20-search-original.md (status).
- docs/demo.md (the lower-bound demo program now gets qualified feedback).
- Regenerated content reports.
- docs/evaluation/l20-original-s1-2026-10-26/.

## 8. Consequence for the demo

`eval/heldout/lower-bound/upper_bound_closed.cpp` is the demo's example of a named diagnosis.
It is still diagnosed as `upper_bound_confusion`, with the same hint. The student message is
now the qualified one, and the attempt adds no `equality_handling` observation. A demo of an
unqualified named diagnosis on lower-bound should use a `stops_at_first_match` program.
