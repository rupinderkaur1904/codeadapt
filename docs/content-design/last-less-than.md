# Content design record: `last-less-than`

> **Update 2026-10-26 (L20 S1 for the original problems, ADR-037).** New content version `ecdcad684935…` (was `4208517a8d24…`). `uses_le` (case O2) and `clamps_to_zero` (case O3) now carry a `known_limitation`: each is output-identical to a program whose cause is a different skill, so their diagnoses are qualified and add no evidence. `equality_handling` becomes positive-only here; `problem_specification` keeps negative evidence through `returns_insertion_point`. Fingerprints and behaviour groups are unchanged; see docs/reviews/2026-10-26/l20-original-s1.md.
>
> **Update 2026-10-26.** New content version `4208517a8d24…` (was `3d52811ae14b…`). The record below describes the problem as designed and is unchanged.
>
> **Banned names (ADR-035).** `banned_names` lists `std::equal_range`, `std::lower_bound`, `std::partition_point`, `std::upper_bound`; an attempt that names one gives no skill observations.
>
> **Positive-only skills (ADR-034).** `search_space_boundaries` has no model that can give negative evidence; the reason is recorded under `positive_only_skills`.

This record was written retrospectively, in CE1.0 (2026-10-17), for content that already
existed. It follows the method in [README.md](README.md). Everything below is measured on
the content as it stands.

- Content version: `3d52811ae14b`.
- Environment: g++ 14.2.0 under runc.
- Live matrix: [../content-reports/last-less-than.md](../content-reports/last-less-than.md).

## 1. Learning objective

**Concept.** Return the largest index `i` with `a[i] < target`, or −1 if there is none. It
is the same partition point as lower-bound, read from the other side: the answer is
`lower_bound − 1`. The problem adds one demand to lower-bound: reading a specification
whose "not found" value (−1) differs from the boundary's natural value (0).

**Subskills.** The four shared skill keys are used.

| Key | What correct code must do here |
| --- | --- |
| `search_space_boundaries` | Let the boundary reach `n`, so that the answer `n − 1` is possible. |
| `loop_termination` | Shrink the range on every iteration. |
| `equality_handling` | Treat equal elements as "not less" (strict `<`). |
| `problem_specification` | Return the index before the boundary, −1 when none, never the boundary itself and never a clamped 0. |

**Prerequisite.** `lower-bound`.

**Not assessed.** O(log n) and midpoint overflow, as in lower-bound.

## 2. Plausible implementation errors

| # | Error pattern | Modelled? | Skill | Measured behaviour |
| --- | --- | --- | --- | --- |
| E1 | `<=` instead of `<` (last ≤ target) | yes: `uses_le` | equality | Differs when the target is present (7 tests, 2 groups) |
| E2 | Returns the boundary instead of boundary − 1 | yes: `returns_insertion_point` | specification | Every answer +1 (15 tests, 5 groups) |
| E3 | Clamps "none" to 0 | yes: `clamps_to_zero` | specification | 0 instead of −1 (6 tests, 2 groups) |
| E4 | `hi = n - 1` with a half-open loop | yes: `hi_init_last_index` | boundaries | Wrong only when the answer is `n − 1` (3 tests, **1 group**). Documented collision. |
| E5 | `lo = mid` | yes: `no_progress_update` | termination | Time limits (9 tests, 3 groups) |
| E6 | `hi = mid - 1` in a half-open loop | **candidate C4** (§7) | boundaries | Measured in a scratch copy: 2 tests, 2 groups |
| E7 | E1 and E3 together | no | several | Abstains; confirmed on held-out `le_and_clamped.cpp` |
| E8 | Linear scan from the right | undetectable | none | Identical output |

## 3. Test audit

There are 15 tests: 2 samples and 13 hidden. All `distinguishes` declarations agree with
the measured matrix.

The tests worth noting:
- `empty` and `below_all` are the minimal −1 cases.
- `equal_first`, `duplicates_all`, `single_equal` and `large_duplicates` are equality
  cases whose answer is −1. They detect both `uses_le` and `clamps_to_zero`, and are
  separated by the other groups.
- `above_all`, `single_below` and `large_above_all` are the only tests whose answer is
  `n − 1`. Together they form a single group, which is why E4 is weak.
- `two_between` is the smallest input on which a non-shrinking update loops.

## 4. Discrimination (measured)

| Model | Detecting tests | Behaviour groups | Weakest pair |
| --- | --- | --- | --- |
| `uses_le` | 7 | 2 | vs `clamps_to_zero`: 7 tests |
| `returns_insertion_point` | 15 | 5 | vs `clamps_to_zero`: 9 tests |
| `clamps_to_zero` | 6 | 2 | vs `uses_le`: 7 tests |
| `hi_init_last_index` | 3 | **1** | vs `no_progress_update`: 9 tests |
| `no_progress_update` | 9 | 3 | vs `hi_init_last_index`: 9 tests |

There are 5 behaviour groups, and no model pair is inseparable.

### 4.1 Ambiguity
- **E4 collides with any error that cannot return `n − 1`.** It is kept as a documented
  limitation: diagnoses are qualified and are not skill evidence (policy 1.2).
- **E2 and E3 are both specification errors.** They are separable: they differ on 9 tests.

### 4.2 Held-out results (v1.1, 2026-10-17)
There are 7 cases. All 5 modelled bugs were diagnosed correctly, the unmodelled double
error abstained, and the correct case passed. All 7 were reproducible over 2 runs.

### 4.3 Errors the suite cannot see
A linear scan (E8).

## 5. From evidence to concepts

| Observed | Hypothesis | Skill | Strength | Next activity |
| --- | --- | --- | --- | --- |
| Wrong when the target is present | E1 | equality | Strong: 2 groups | count-occurrences, which has 9 equality tests |
| Every answer +1 | E2 | specification | Strong: 5 groups | count-occurrences, whose difference of boundaries exercises the specification |
| 0 instead of −1 | E3 | specification | Strong: 2 groups | count-occurrences |
| Wrong only when the answer is `n − 1` | E4, or another such error | boundaries | **Weak**: qualified | lower-bound's `above_all` tests; later G1 |
| Time limits | E5 | termination | Medium | G2, when it exists |
| None of the above | unmodelled | none claimed | — | Retry; flagged for review |

## 6. Follow-up and curriculum links

| Relation | Current | Gap |
| --- | --- | --- |
| Prerequisite | lower-bound | G1, "first true" (CE1.1) |
| Equivalent | count-occurrences | — |
| Transfer | none | G3 (CE1.3) |
| Reassesses | lower-bound's skills, with a different "not found" convention | — |

## 7. Proposed changes and known limitations

**C4 (proposed, not applied): add `hi_skips_candidate` as a boundary model.**
- **Measured in a scratch copy:** detected by `duplicates_middle` and `two_between`. That
  is 2 behaviour groups. It is separated from every existing model by at least 5 tests;
  the weakest pair is `hi_init_last_index`.
- **Why it matters:** as with C3, it would make boundary failures observable here
  without a documented collision.
- **Cost:**
  - It changes the content version.
  - It needs two `distinguishes` updates.
  - Only two tests detect it, so the support is minimal.
- **Status:** awaits an owner decision.

**Known limitations.**
- E4 is weak by design.
- Termination errors are seen only as time limits.
- Complexity is not assessed.
- The held-out cases were written by the models' author.
