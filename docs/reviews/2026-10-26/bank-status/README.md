# Problem bank status matrix: 25 problems (2026-10-26)

**Status.** Review only (owner request 2026-10-26 05:22, task 4). No problem, mapping,
recommendable flag or review status was changed by this review.

**No problem is research-validated.** Passing tests, content validation and author-written
held-out results are engineering checks, not validation on independent or real-student
programs.

**How it was made.** `python3 docs/reviews/2026-10-26/bank-status/bank_matrix.py` writes the
table below. The script reads:
- content/demo/*/problem.toml;
- the regenerated docs/content-reports/;
- eval/heldout/;
- `effective_positive_only.py` (docs/evaluation/l20-original-s1-2026-10-26/).

Some columns restate committed decisions: the review column, the alternative-cause column and
the mapping flags.

**Reading the columns.**
- **Contract and edge-case tests:** the number of committed tests, with how many are visible
  samples and how many are large. "Empty input" means a test input of length 0, detected from
  the input string. A "no" can be correct: several contracts require a non-empty array.
- **Fingerprints:** the number of error models, and the range of measured behaviour groups
  per model. Every pair of models is separable on at least one test (content validation and
  `tests/sandbox/test_demo_content.py`).
- **Held-out:** the number of committed held-out programs. All were written by the error-model
  author.
- **Positive-only (declared):** a skill with a `positive_only_skills` reason in problem.toml.
  The content check enforces these.
- **Positive-only (effective):** a skill with no declared reason whose every model can still
  never be named unqualified by diagnosis v1.3. The reasons are rule 4b (a time-limit
  fingerprint), rule 7 (fewer than 2 detecting tests), a single behaviour group, or rule 8a (a
  constant prediction). The content check does not see these (§3).

| ID and version | Family | Reference / content validation | Contract and edge-case tests | Fingerprints and alternative-cause review | Skill-mapping validity | Banned names | Research review status | Recommendable | Outstanding limitations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `closest-pair-sum` `dfc45a07cd00` | two-pointers | valid (0 errors, 0 warnings, 0 documented limitations) | 13 (2 sample, 2 large); empty input no | 4 models, groups 4–5; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 8 author-written | no | — |
| `container-water` `e9fc3901bd29` | two-pointers | valid (0 errors, 0 warnings, 0 documented limitations) | 13 (2 sample, 2 large); empty input no | 4 models, groups 2–5; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 8 author-written | no | known_limitation: `moves_taller`; positive-only (declared): pointer_movement |
| `count-occurrences` `4666e07e237c` | binary-search | valid (0 errors, 0 warnings, 1 documented limitations) | 15 (2 sample, 3 large); empty input yes | 4 models, groups 1–4; exhaustive + random search 2026-10-26 (l20-search-original.md) | author-defined, unvalidated (L10/L22) | 4 | owner-accepted content and held-out set (CE0/CE1.1); held-out 6 author-written | yes | known_limitation: `hi_init_last_index`; positive-only (declared): search_space_boundaries; positive-only (effective, rules 4b/7/8a): equality_handling, loop_termination |
| `dedup-sorted` `89b894b4693d` | two-pointers | valid (0 errors, 0 warnings, 0 documented limitations) | 12 (2 sample, 2 large); empty input no | 4 models, groups 3–6; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 1 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 8 author-written | no | known_limitation: `returns_last_index`; positive-only (declared): output_contract |
| `distinct-in-windows` `7948c0fabbdf` | sliding-window | valid (0 errors, 0 warnings, 0 documented limitations) | 12 (2 sample, 2 large); empty input no | 3 models, groups 2–4; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 7 author-written | no | — |
| `exact-search` `94bfc112e9e7` | binary-search | valid (0 errors, 0 warnings, 0 documented limitations) | 19 (2 sample, 4 large); empty input yes | 6 models, groups 2–6; exhaustive + random search 2026-10-25 (l20-search.md; recheck 2026-10-26) | author-defined, unvalidated (L10/L22) | 6 | **Unreviewed** (provisional, owner 2026-10-25 07:50); held-out 7 author-written | no | known_limitation: `lo_init_one`, `swapped_direction`; positive-only (declared): search_space_boundaries |
| `first-max-index` `50798634a3ef` | arrays | valid (0 errors, 0 warnings, 0 documented limitations) | 14 (2 sample, 2 large); empty input no | 4 models, groups 2–6; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 1 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 8 author-written | no | — |
| `first-true` `c5285489e34a` | binary-search | valid (0 errors, 0 warnings, 1 documented limitations) | 19 (2 sample, 4 large); empty input yes | 9 models, groups 1–8; exhaustive + random search 2026-10-26 (l20-search-original.md) | author-defined, unvalidated (L10/L22) | 5 | owner-accepted content and held-out set (CE0/CE1.1); held-out 7 author-written | no | known_limitation: `hi_init_last_index`, `none_sentinel` |
| `integer-sqrt` `01edbe01d8a8` | binary-search | valid (0 errors, 0 warnings, 0 documented limitations) | 19 (2 sample, 0 large); empty input no | 8 models, groups 2–12; exhaustive + random search 2026-10-25 (l20-search.md; recheck 2026-10-26) | author-defined, unvalidated (L10/L22) | 6 | **Unreviewed** (provisional, owner 2026-10-25 07:50); held-out 8 author-written | no | known_limitation: `strict_square_test`; positive-only (declared): equality_handling |
| `last-less-than` `ecdcad684935` | binary-search | valid (0 errors, 0 warnings, 1 documented limitations) | 15 (2 sample, 3 large); empty input yes | 5 models, groups 1–5; exhaustive + random search 2026-10-26 (l20-search-original.md) | author-defined, unvalidated (L10/L22) | 4 | owner-accepted content and held-out set (CE0/CE1.1); held-out 7 author-written | yes | known_limitation: `clamps_to_zero`, `hi_init_last_index`, `uses_le`; positive-only (declared): equality_handling, search_space_boundaries; positive-only (effective, rules 4b/7/8a): loop_termination |
| `last-occurrence` `441ef3b2b697` | binary-search | valid (0 errors, 0 warnings, 1 documented limitations) | 19 (2 sample, 3 large); empty input yes | 6 models, groups 1–6; exhaustive + random search 2026-10-25 (l20-search.md; recheck 2026-10-26) | author-defined, unvalidated (L10/L22) | 5 | **Unreviewed** (provisional, owner 2026-10-25 07:50); held-out 8 author-written | no | known_limitation: `hi_init_last_index`, `missing_equality_check`, `returns_first_occurrence`, `stops_at_any_match`; positive-only (declared): equality_handling, search_space_boundaries; positive-only (effective, rules 4b/7/8a): loop_termination |
| `longest-run` `1a66ed58fae9` | arrays | valid (0 errors, 0 warnings, 0 documented limitations) | 13 (2 sample, 2 large); empty input no | 4 models, groups 2–6; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 8 author-written | no | — |
| `longest-sum-at-most` `da1fb518004a` | sliding-window | valid (0 errors, 0 warnings, 0 documented limitations) | 14 (2 sample, 2 large); empty input no | 3 models, groups 2–4; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 7 author-written | no | — |
| `lower-bound` `8ca53699ef0d` | binary-search | valid (0 errors, 0 warnings, 1 documented limitations) | 17 (2 sample, 3 large); empty input yes | 8 models, groups 1–11; exhaustive + random search 2026-10-26 (l20-search-original.md) | author-defined, unvalidated (L10/L22) | 4 | owner-accepted content and held-out set (CE0/CE1.1); held-out 12 author-written | yes | known_limitation: `hi_init_last_index`, `upper_bound_confusion`; positive-only (effective, rules 4b/7/8a): loop_termination |
| `max-window-sum` `6a286840ec62` | sliding-window | valid (0 errors, 0 warnings, 0 documented limitations) | 12 (2 sample, 2 large); empty input no | 4 models, groups 2–5; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 8 author-written | no | — |
| `min-capacity` `e7f55817f3b0` | binary-search | valid (0 errors, 0 warnings, 0 documented limitations) | 19 (2 sample, 4 large); empty input no | 6 models, groups 2–6; exact equivalence argument (ADR-032) | author-defined, unvalidated (L10/L22); flag: two equality models non-unique (ADR-032) | 4 | **Unreviewed** (provisional, owner 2026-10-25 07:50); held-out 8 author-written | no | known_limitation: `full_day_overflows`, `strict_day_limit`; positive-only (declared): equality_handling; positive-only (effective, rules 4b/7/8a): loop_termination |
| `peak-index` `5963188f0a4a` | binary-search | valid (0 errors, 0 warnings, 0 documented limitations) | 16 (2 sample, 4 large); empty input no | 5 models, groups 2–6; exhaustive + random search 2026-10-25 (l20-search.md; recheck 2026-10-26) | author-defined, unvalidated (L10/L22) | 4 | **Unreviewed** (provisional, owner 2026-10-25 07:50); held-out 8 author-written | no | known_limitation: `swapped_direction` |
| `pivot-index` `28eef0379d7c` | prefix-sums | valid (0 errors, 0 warnings, 0 documented limitations) | 15 (2 sample, 3 large); empty input no | 4 models, groups 2–3; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22); judgement for review: four probes all mapped to range_inclusion (ADR-034) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 8 author-written | no | — |
| `plus-one` `a7518c266db6` | arrays | valid (0 errors, 0 warnings, 0 documented limitations) | 13 (2 sample, 2 large); empty input no | 4 models, groups 2–6; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22); judgement for review: `adds_at_front` mapped to loop_bounds (ADR-034) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 8 author-written | no | — |
| `range-sum-queries` `74d198449c3a` | prefix-sums | valid (0 errors, 0 warnings, 0 documented limitations) | 10 (2 sample, 1 large); empty input no | 3 models, groups 2–3; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 7 author-written | no | — |
| `rotated-min` `6df29dcd99d7` | binary-search | valid (0 errors, 0 warnings, 1 documented limitations) | 18 (2 sample, 4 large); empty input no | 5 models, groups 1–5; skill-mapping review 2026-10-25 only; no exhaustive search | author-defined, unvalidated (L10/L22); flag: `compares_with_lo` attributed to its effect (search_space_boundaries), not its cause | 4 | **Unreviewed** (provisional, owner 2026-10-25 07:50); held-out 8 author-written | no | known_limitation: `hi_skips_candidate`; positive-only (effective, rules 4b/7/8a): loop_termination |
| `rotated-search` `14e8af1098ad` | binary-search | valid (0 errors, 0 warnings, 1 documented limitations) | 21 (2 sample, 4 large); empty input no | 5 models, groups 1–7; exhaustive + random search 2026-10-25 (l20-search.md; recheck 2026-10-26) | author-defined, unvalidated (L10/L22) | 5 | **Unreviewed** (provisional, owner 2026-10-25 07:50); held-out 8 author-written | no | known_limitation: `left_half_test_strict`, `left_range_excludes_lo`; positive-only (declared): equality_handling |
| `second-largest` `6f9032b8d8b8` | arrays | valid (0 errors, 0 warnings, 0 documented limitations) | 14 (2 sample, 2 large); empty input no | 4 models, groups 2–3; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 8 author-written | no | — |
| `stock-profit` `25a63d1ddab3` | arrays | valid (0 errors, 0 warnings, 0 documented limitations) | 13 (2 sample, 2 large); empty input no | 3 models, groups 2–3; 400 random inputs per design record (not exhaustive) | author-defined, unvalidated (L10/L22) | 0 | bank expansion 2026-10-25; not owner-reviewed for research use; held-out 7 author-written | no | known_limitation: `ignores_order` |
| `upper-bound` `b429912d241e` | binary-search | valid (0 errors, 0 warnings, 0 documented limitations) | 19 (2 sample, 4 large); empty input yes | 7 models, groups 2–8; exhaustive + random search 2026-10-25 (l20-search.md; recheck 2026-10-26) | author-defined, unvalidated (L10/L22) | 4 | **Unreviewed** (provisional, owner 2026-10-25 07:50); held-out 7 author-written | no | known_limitation: `hi_init_last_index`, `lower_bound_confusion`, `none_sentinel`; positive-only (declared): equality_handling; positive-only (effective, rules 4b/7/8a): loop_termination |

## 1. Points that need attention

**The eight provisional binary-search problems.** These are integer-sqrt, min-capacity,
upper-bound, exact-search, last-occurrence, rotated-min, rotated-search and peak-index.
- They are still labelled **Unreviewed** in the problem list. `web/src/pages/
  ProblemListPage.tsx` holds the set, and `ResearchPage.test.tsx` pins it.
- They are `recommendable = false`, and their held-out sets are author-written and not
  owner-accepted.
- rotated-min had no exhaustive alternative-cause search. Its `compares_with_lo` mapping flag
  (effect, not cause) is open.
- Nothing in this stage changed them.

**pivot-index.** Every declared skill has an evidence-capable model:
- `range_inclusion` through `pivot_counted_left` and `pivot_counted_right`;
- the other two skills through their own models.

`test_pivot_index_has_models_for_its_mapped_skill` pins this. Mapping all four former
`index_range` and `update_rule` probes to `range_inclusion` is the ADR-034 judgement that
awaits review. It is not a defect.

**Positive-only skills.**
- **Declared:** 12 skills in 10 problems carry a written reason, after ADR-037 added
  last-less-than `equality_handling`.
- **Effective:** 8 more skills in 7 problems are positive-only in practice, but not declared.
  They are listed in §3.

**Known limitations.** 27 models in 15 problems carry a `known_limitation`, for one of two
reasons:
- a single behaviour group (for example `hi_init_last_index`);
- a non-unique attribution (ADR-032, ADR-036, ADR-037, and the three bank-expansion cases).

first-true `returns_any_true` also has an accepted false negative (CE1.1): it abstains rather
than naming. That is recorded in docs/content-design/first-true.md, not as a
`known_limitation`.

**Content that could fail to load.** All 25 directories load: the unit suite loads the
catalogue in every run, and the API starts.

The loader (`content/loader.py`) rejects a problem whose statement has a "Do not call …"
sentence that does not match `banned_names`. The error is raised inside `load_catalogue`, so
one such problem stops the whole catalogue loading, and the API with it. This fails closed,
and it is the intended check.

It is a risk only for new content. Only the exact phrase "Do not call" is parsed: a statement
that bans calls in other words ("must not use") would not be checked. None of the 25
statements uses another phrasing (searched 2026-10-26).

## 2. Research review status by group

| Group | Problems | Status |
| --- | --- | --- |
| Original | lower-bound, count-occurrences, last-less-than, first-true | Content and held-out sets accepted by the owner (CE0, CE1.1). lower-bound, count-occurrences and last-less-than are recommendable; first-true is not (E2). |
| Provisional binary search | the eight above | **Unreviewed**: kept pending owner review (2026-10-25 07:50), not research-validated. |
| Bank expansion | 13 problems in arrays, two-pointers, sliding-window and prefix-sums | Built on the owner's 2026-10-25 directive and content-validated. Not owner-reviewed for research use; skill keys unvalidated (L22); not recommendable (L21). |

## 3. Effective positive-only skills (not declared)

Each skill below has no `positive_only_skills` reason. Its only models can never give an
`incorrect` observation, because diagnosis v1.3 never names them unqualified. The
`incorrect` evidence these skills lack is withheld by the diagnosis rules (ADR-027, ADR-030).
Nothing has changed in their behaviour.

| Problem | Skill | Why no model gives negative evidence |
| --- | --- | --- |
| count-occurrences | equality_handling | `upper_uses_strict` predicts 0 on every test (rule 8a) |
| count-occurrences, last-less-than, last-occurrence, min-capacity, rotated-min | loop_termination | `no_progress_update` times out (rule 4b) |
| lower-bound, upper-bound | loop_termination | `no_progress_update` and `closed_loop_hi_mid` time out (rule 4b) |

Output of `effective_positive_only.py`, reproduced in
docs/evaluation/l20-original-s1-2026-10-26/effective_positive_only.txt.

**Proposed, not implemented:** extend the `positive_only_skills` check to these cases. It
would need the measured fingerprints, so it belongs in `codeadapt-content validate` or
`tests/sandbox/test_demo_content.py`, not in the static ProblemSpec check.

Implementing it would add 8 written reasons to 7 problems. That would give those problems
new content versions without any change in behaviour, so it is left for an owner decision.
