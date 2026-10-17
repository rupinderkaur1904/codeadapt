# Content design record: `count-occurrences`

This record was written retrospectively, in CE1.0 (2026-10-17), for content that already
existed. It follows the method in [README.md](README.md). Where the method says a record
comes before the content, that was not possible here; everything below is measured on the
content as it stands.

- Content version: `d1b043c04574`.
- Environment: g++ 14.2.0 under runc.
- Live matrix: [../content-reports/count-occurrences.md](../content-reports/count-occurrences.md).

## 1. Learning objective

**Concept.** Count the elements equal to `target` in a sorted array in O(log n) time. The
count is the difference between two partition points: the first index with
`a[i] > target` minus the first index with `a[i] >= target`. The problem reuses the
lower-bound idea twice and adds one new demand: choosing the right comparison for each
boundary.

**Subskills.** The four shared skill keys are used.

| Key | What correct code must do here |
| --- | --- |
| `search_space_boundaries` | Let both boundaries reach `n`, so a run of the target at the end is counted in full. |
| `loop_termination` | Shrink the range on every iteration of both searches. |
| `equality_handling` | Send equal elements left for the lower boundary and right for the upper one. |
| `problem_specification` | Return the difference of two half-open boundaries: 0 when absent, never a +1 or −1 correction. |

**Prerequisite.** `lower-bound`. The `[curriculum]` section lists it.

**Not assessed.**
- The O(log n) requirement. A linear count gives identical output (§4.3).
- Midpoint overflow, which is infeasible at these sizes.

## 2. Plausible implementation errors

| # | Error pattern | Modelled? | Skill | Measured behaviour |
| --- | --- | --- | --- | --- |
| E1 | Same strict comparison `<` for both boundaries, so the count is always 0 | yes: `upper_uses_strict` | equality | 0 whenever the target is present (9 tests, 2 groups) |
| E1′ | Same non-strict comparison `<=` for both boundaries | no (collides with E1) | equality | Also 0 whenever present: identical output, same skill. Kept as an intended ambiguity, since the diagnosis names the same skill. |
| E2 | `hi = n - 1` with a half-open loop | yes: `hi_init_last_index` | boundaries | Undercounts only when the run reaches the end (5 tests, **1 group**). Documented collision. |
| E3 | `lo = mid` instead of `mid + 1` | yes: `no_progress_update` | termination | Time limit when a search moves right with two candidates left (13 tests, 3 groups) |
| E4 | `upper - lower + 1` | yes: `inclusive_count` | specification | Every answer one too large (15 tests, 4 groups) |
| E5 | `hi = mid - 1` in a half-open loop | **candidate C3** (§7) | boundaries | Measured in a scratch copy: 4 tests, 2 groups |
| E6 | Returns presence (0 or 1) instead of a count | no | specification | Abstains as unmodelled; confirmed on held-out `presence_only.cpp` |
| E7 | Lower bound, then a linear walk over the run | undetectable | none | Identical output on every test |
| E8 | Subtracts in the wrong order (negative counts) | no | specification | Distinct output; would abstain as unmodelled |
| E9 | Two errors at once | no | several | Outside the single-error space |

## 3. Test audit

There are 15 tests: 2 samples and 13 hidden. Every test's `distinguishes` field agrees with
the measured matrix (validation passes with 0 errors).

The tests worth noting:
- `unique_middle` separates equality errors from end-of-array errors.
- `run_at_start` gives equality evidence without the end boundary.
- `run_at_end`, `all_equal`, `single_equal` and `two_equal` are the only tests that need
  a boundary at `n`. Together they form a single behaviour group, which is why E2 is weak.
- `empty` and `below_all` detect only `inclusive_count`.
- The three `large_*` tests are scale cases. They do not test complexity.

## 4. Discrimination (measured)

| Model | Detecting tests | Behaviour groups | Weakest pair |
| --- | --- | --- | --- |
| `upper_uses_strict` | 9 | 2 | vs `hi_init_last_index`: 8 tests |
| `hi_init_last_index` | 5 | **1** | vs `upper_uses_strict`: 8 tests |
| `no_progress_update` | 13 | 3 | vs `hi_init_last_index`: 13 tests |
| `inclusive_count` | 15 | 4 | all pairs 15 tests |

There are 4 behaviour groups, and no model pair is inseparable.

### 4.1 Ambiguity
- **E2 collides with any unmodelled error that cannot place a boundary at `n`**, for
  example a clamped result. It is kept as a documented limitation: diagnoses are
  qualified, shown to the student as a hint and never counted as skill evidence (ledger
  policy 1.2).
- **E1 and E1′ produce identical output.** This is acceptable because both are the same
  skill.

### 4.2 Held-out results (v1.1, 2026-10-17)
There are 6 cases. All 4 modelled bugs were diagnosed correctly, the unmodelled case
abstained, and the correct case passed. All 6 were reproducible over 2 runs. Source:
`docs/evaluation/ce1.0-2026-10-17/`.

### 4.3 Errors the suite cannot see
- A linear scan (E7).
- Any error that only shows on inputs larger than the memory limit allows.

## 5. From evidence to concepts

| Observed | Hypothesis | Skill | Strength | Next activity |
| --- | --- | --- | --- | --- |
| 0 whenever present | E1 (or E1′) | equality | Strong: 2 groups | last-less-than, which has 7 equality tests |
| Undercount only on runs at the end | E2, or another "cannot reach n" error | boundaries | **Weak**: 1 group, qualified | A problem whose answer is `n` in another form. Today that is lower-bound's `above_all` tests; later G1. |
| Time limits | E3 | termination | Medium: time limits are non-specific | G2, when it exists |
| Every answer +1 | E4 | specification | Strong: 4 groups | last-less-than, whose −1 convention exercises the specification |
| None of the above | unmodelled | none claimed | — | Retry with test feedback; flagged for review |

## 6. Follow-up and curriculum links

| Relation | Current | Gap |
| --- | --- | --- |
| Prerequisite | lower-bound | G1, "first true", would be a gentler step back (CE1.1) |
| Equivalent | last-less-than | — |
| Transfer | none | G3, "minimum feasible capacity" (CE1.3) |
| Reassesses | lower-bound's equality and boundary skills, in a two-boundary setting | — |

The follow-up criterion is the one shared by the family: every reliable follow-up test that
probes the diagnosed skill passes, and no model of that skill is diagnosed.

## 7. Proposed changes and known limitations

**C3 (proposed, not applied): add `hi_skips_candidate` as a boundary model.**
- **Measured in a scratch copy:** detected by `sample_run`, `unique_middle`, `run_at_end`
  and `large_unique`. That is 2 behaviour groups. It is separated from every existing
  model by at least 8 tests.
- **Why it matters:** it would make boundary failures observable in this problem without
  a documented collision. This addresses CE1 gap 1, under which boundary failures are
  observable today only in lower-bound.
- **Cost:**
  - It changes this problem's content version.
  - It needs four `distinguishes` updates.
  - Students who make this error would get a boundary diagnosis instead of whatever the
    current models give for it. That outcome was not measured, and it is not a diagnosis
    of this error, since no current model describes it.
- **Status:** awaits an owner decision, because it changes an existing content version.

**Known limitations.**
- E2 is weak by design.
- Time limits are the only signature of termination errors.
- Complexity is not assessed.
- The held-out cases were written by the models' author.
