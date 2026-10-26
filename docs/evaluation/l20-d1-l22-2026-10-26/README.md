# Re-run after L20 S1, D1 and the L22 taxonomy migration (2026-10-26)

**Why.** ADR-034, ADR-035 and ADR-036 changed problem.toml in all 25 problems:

- `known_limitation` on 11 models;
- `banned_names` in 14 problems;
- new skill keys in 13 problems;
- `positive_only_skills` reasons in 10 problems.

So every problem has a new content version. The diagnosis methods read none of these fields,
so diagnoses were expected to be unchanged. This record checks that, along with the other
behaviour the changes were not meant to alter. **All earlier evaluation records are
preserved unchanged.**

**Environment.** g++ 14.2.0, `runc`, image `codeadapt-sandbox:gcc14.2-1`, 2 runs per case.

## Content versions

| Problem | Previous version | New version | A: S1 limitation | B: banned names | C: taxonomy | Positive-only skills |
| --- | --- | --- | --- | --- | --- | --- |
| closest-pair-sum | `de254fa1d64b` | `dfc45a07cd00` | — | — | yes | — |
| container-water | `bbac030fbe03` | `e9fc3901bd29` | — | — | yes | `pointer_movement` |
| count-occurrences | `d1b043c04574` | `4666e07e237c` | — | 4 | — | `search_space_boundaries` |
| dedup-sorted | `bb981b9b5617` | `89b894b4693d` | — | 1 | yes | `output_contract` |
| distinct-in-windows | `e3bcaf715296` | `7948c0fabbdf` | — | — | yes | — |
| exact-search | `9cdc3cfe5d92` | `94bfc112e9e7` | `swapped_direction`, `lo_init_one` | 6 | — | `search_space_boundaries` |
| first-max-index | `cb56cfeafe27` | `50798634a3ef` | — | 1 | yes | — |
| first-true | `b69c5efa3b39` | `485c974b4928` | — | 5 | — | — |
| integer-sqrt | `e6f66ab25569` | `01edbe01d8a8` | `strict_square_test` | 6 | — | `equality_handling` |
| last-less-than | `3d52811ae14b` | `4208517a8d24` | — | 4 | — | `search_space_boundaries` |
| last-occurrence | `d6d9106ea7d6` | `441ef3b2b697` | `returns_first_occurrence`, `stops_at_any_match`, `hi_init_last_index` | 5 | — | `equality_handling`, `search_space_boundaries` |
| longest-run | `2f41017cdef4` | `1a66ed58fae9` | — | — | yes | — |
| longest-sum-at-most | `e0e0e4027d7b` | `da1fb518004a` | — | — | yes | — |
| lower-bound | `871602bc2bba` | `9aade9e1396e` | — | 4 | — | — |
| max-window-sum | `7e1c6d851a9c` | `6a286840ec62` | — | — | yes | — |
| min-capacity | `63287d727b7b` | `e7f55817f3b0` | — | 4 | — | `equality_handling` |
| peak-index | `5e3ced93c8c1` | `5963188f0a4a` | `swapped_direction` | 4 | — | — |
| pivot-index | `28c6008e1984` | `28eef0379d7c` | — | — | yes | — |
| plus-one | `53ce6c46a11b` | `a7518c266db6` | — | — | yes | — |
| range-sum-queries | `d47598c44246` | `74d198449c3a` | — | — | yes | — |
| rotated-min | `c9f3b5c9fcac` | `6df29dcd99d7` | — | 4 | — | — |
| rotated-search | `8568f135e8ad` | `14e8af1098ad` | `left_range_excludes_lo` | 5 | — | `equality_handling` |
| second-largest | `15b0c500f154` | `6f9032b8d8b8` | — | — | yes | — |
| stock-profit | `0c509afe798c` | `25a63d1ddab3` | — | — | yes | — |
| upper-bound | `38082888c308` | `b429912d241e` | `lower_bound_confusion`, `hi_init_last_index`, `none_sentinel` | 4 | — | `equality_handling` |

"B: banned names" gives the number of names listed. The earlier versions stay registered,
with their own skill-map snapshots (ADR-023 D4).

## 1. Held-out cases: diagnoses unchanged

**Command** (from `backend/`, for each problem `<p>` in `eval/heldout/`):

```
uv run codeadapt-eval --content ../content/demo --heldout ../eval/heldout --problem <p> \
  --runs 2 --compare v1.1 v1.2 v1 --json ../docs/evaluation/l20-d1-l22-2026-10-26/heldout/<p>.json \
  --markdown ../docs/evaluation/l20-d1-l22-2026-10-26/heldout/<p>.md
```

**Comparison** (`python3 docs/evaluation/l20-d1-l22-2026-10-26/compare_heldout.py`, output in
`heldout_comparison.txt`). It covers 582 case × method results: 194 cases under v1.1, v1.2
and v1.3. Each is compared with the latest earlier record of the same case, which are:

- `adr030-2026-10-23`;
- `ce1.2-2026-10-24`;
- `ce2-2026-10-24`;
- `expansion-2026-10-25` (second-largest v2);
- `adr032-2026-10-25`.

**Result:** 582 identical, 0 changed, 0 missing. Outcome, named model, candidates,
classification and reproducibility are all identical.

**Synthetic, author-written cases.** This is not an accuracy estimate for real students.

## 2. Content reports: measurements unchanged

`codeadapt-content report content/demo --out docs/content-reports` (log:
`content-report.log`) regenerated all 25 reports, and every problem validates (`RESULT ok`).

The regenerated reports change in only two ways:

- each report's content version;
- the skill and limitation columns of the remapped or newly limited models.

The fingerprint matrices, detecting-test counts, behaviour groups, pairs and validation
results are unchanged, checked line by line against the previous HEAD.

## 3. Recommendations: choices unchanged

`recommendation_regression.py` was run at the previous HEAD (57b46d1) and at this change. It
covers 442 one-attempt synthetic histories, every problem with: no failure, unmodelled,
every model named, and every model pair ambiguous. `compare_recommendations.py` compares
them (`recommendation_comparison.txt`).

- **Rule, action, chosen problem and review flag:** identical in all 442 cases.
- **Skill names:** in 88 cases only the target and criterion skill names differ, because
  they are the ADR-034 keys.

The qualified rationale for the 11 S1 models is the intended ADR-036 change, and is not
compared here.

## 4. Banned names in stored evaluation programs

`banned_name_replay.py` (`banned_name_replay.txt`) applies the ADR-035 detector to every
stored evaluation program: held-out, calibration and mutation.

- **Programs:** 845, of which 761 belong to a problem that bans names.
- **Programs that name a banned call of their problem:** 0.

No evaluation result changes under the new eligibility rule.

## Not covered

- **Real-student accuracy and calibrated mastery:** none claimed. The BKT parameters
  (`bkt-params-assumed-1`) are unchanged.
- **Attempts in dev and test databases:** not replayed. Their versions predate the change,
  so they keep their evidence (ADR-035).
