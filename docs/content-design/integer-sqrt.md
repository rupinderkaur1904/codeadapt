# Content design record: `integer-sqrt` (CE1.2, gap G2)

> **Update 2026-10-26.** New content version `01edbe01d8a8…` (was `e6f66ab25569…`). The record below describes the problem as designed and is unchanged.
>
> **L20 safeguard S1 (ADR-036).** `strict_square_test` now carries a `known_limitation` (a cross-skill twin, docs/reviews/2026-10-25/l20-search.md); diagnoses are qualified and add no negative evidence.
>
> **Banned names (ADR-035).** `banned_names` lists `cbrt`, `hypot`, `pow`, `sqrt`, `sqrtf`, `sqrtl`; an attempt that names one gives no skill observations.
>
> **Positive-only skills (ADR-034).** `equality_handling` has no model that can give negative evidence; the reason is recorded under `positive_only_skills`.

**Status.** This record was committed before the problem's content was written or measured
and before any held-out case was run. The matrix in §4.1 is a **design-time prediction**:
a Python re-implementation of each planned model, used to choose tests. It is not the
sandbox measurement. The measured matrix is added in §4.2 after validation, and wherever
the two disagree, the measurement wins.

## 1. Learning objective

**Concept.** Binary search over an *answer range* rather than over an array. The task is
to return the largest `r` with `r * r <= x`, which is a partition point of the monotone
predicate `r * r <= x` over `r = 0 .. x`. There is no array to index, and the predicate
needs 64-bit arithmetic.

**Why this problem (gap G2, and gap 1).**
- **Termination evidence beyond time limits.** Every termination model in the bank today
  is seen only as a time limit. Here the answer range is large and the loop bound is
  explicit, so several plausible termination errors *terminate with a wrong answer*:
  - a loop condition that stops before the last candidate is checked;
  - a fixed iteration count too small for the range.
  These produce output signatures, which are more specific than a time limit.
- **Boundary failures outside lower-bound and first-true.** The range's upper end is a
  plausible place to cut a candidate off.

**Contract.**

```cpp
int int_sqrt(int x);
```

- `0 <= x <= 2^31 - 1`. The function returns `floor(sqrt(x))`, which is at most 46340.
- The statement says `mid * mid` must be computed in 64-bit arithmetic (`long long`),
  since `46341 * 46341` overflows `int`.
- The statement asks for O(log x) and forbids `sqrt`, `sqrtf`, `sqrtl`, `pow`, `cbrt` and
  `hypot`. The harness cannot enforce either rule; see §4.4.

**Subskills.** These are the four existing skill keys. No new skill is proposed (§2).

| Key | What correct code must do here |
| --- | --- |
| `search_space_boundaries` | Keep every candidate answer in range: 0 and 1 at the bottom, 46340 at the top. |
| `loop_termination` | Keep searching until exactly one candidate remains: no unchecked last candidate, no iteration cap, and progress on every step. |
| `equality_handling` | Accept `r` when `r * r == x`: a perfect square is its own answer's square. |
| `problem_specification` | Return the floor: never the ceiling, never the first `r` that is too large. |

**Prerequisites assumed.** Binary search over an array (lower-bound or first-true), `long
long`, and integer overflow.

**Not assessed.**
- O(log x): a linear scan up to 46340 is fast enough and gives identical output.
- Floating-point `sqrt`: it is correct on this whole range and gives identical output.

## 2. Plausible implementation errors

Reference form: a closed interval `[0, x]` with a running answer. A candidate `mid` with
`mid * mid <= x` is recorded and the search moves right; otherwise it moves left.

| # | Error pattern | Model key | Skill | Predicted behaviour |
| --- | --- | --- | --- | --- |
| Q1 | Accepts only `mid * mid < x` (strict) | `strict_square_test` | equality | `r - 1` on every perfect square ≥ 1 |
| T1 | Closed interval with a running answer, but the loop is `while (lo < hi)`, so the last candidate is never checked | `closed_loop_lt` | termination | Wrong output (one too small) whenever the answer is only confirmed at the last step; terminates |
| T2 | A fixed 16 iterations instead of "until the range is empty" (the answer is below 2^16, but the range is `[0, x]`) | `fixed_iterations_16` | termination | Wrong output for large `x`; terminates |
| T3 | `lo = mid` with a floor midpoint, in the "last true" form | `floor_mid_no_progress` | termination | Time limit once `hi == lo + 1` and `lo` is valid |
| B1 | Half-open "first `r` with `r * r > x`" search, minus one, with `hi = x` instead of `x + 1` | `hi_excludes_x` | boundaries | Wrong only for `x = 0` (-1) and `x = 1` (0) |
| B2 | The same half-open form, with the range capped at `hi = 46340` instead of 46341 to avoid overflow | `hi_cap_46340` | boundaries | 46339 instead of 46340 for every `x >= 46340^2` |
| S1 | Returns the smallest `r` with `r * r >= x` (the ceiling, a lower-bound habit) | `returns_ceiling` | specification | `r + 1` on every non-square |
| S2 | Closed interval with no running answer, returning `lo` | `returns_lo_closed` | specification | Always `r + 1` |
| U1 | `int` product `mid * mid` (signed overflow) | not modelled | — | Undefined behaviour; output depends on the optimiser. Recorded, never modelled (CE1 plan). |
| U2 | `unsigned` 32-bit product, which wraps | not modelled | — | Defined but wrong for large `x`. See the taxonomy note below. |
| U3 | Newton's method, floating-point `sqrt`, linear scan | undetectable when correct | — | Identical output |
| U4 | Two errors at once | not modelled | several | Should abstain as unmodelled |

**Skill taxonomy check.**
- Every modelled error is described by one of the four existing keys.
- **The one candidate gap is integer range (U1, U2).** These are arithmetic-range errors:
  - They are not about search boundaries, termination, equality or specification.
  - Describing them would need a new skill.
  - **They are not modelled.** No new skill is proposed in this stage. A U2 case is among
    the held-out cases (§7) to check that the method abstains on it.
  - If a later stage needs overflow evidence, that is a taxonomy decision for the owner.
- **T1 and T2 are assigned to `loop_termination`.** The skill is "each iteration shrinks
  the search space so the loop terminates". Here the loop terminates, but in the wrong
  place, before exactly one candidate remains. The existing skill text covers the
  shrinking, not *where* the loop stops; first-true's `stops_one_early` made the same
  assignment.
  - This is a stretch of the skill's wording, not a new skill.
  - If measurement shows T1 or T2 confused with a boundary model, it will be revisited.

## 3. Test strategy

There are 19 tests: 2 samples (`eight`, `sixteen`) and 17 hidden. Each test's input is a
single integer `x`. Answers covered: 0, 1, small values, 1000, 11111, 46339 and 46340.

| Test | x | Answer | Why |
| --- | ---: | ---: | --- |
| `zero` | 0 | 0 | B1's -1; S2's 1 |
| `one` | 1 | 1 | B1, T1, Q1, T3: smallest square, and the smallest range where the last-candidate check matters |
| `two`, `three` | 2, 3 | 1 | Small non-squares |
| `four`, `nine`, `sixteen`, `hundred` | | | Small perfect squares (Q1, T1) |
| `eight`, `ten`, `fifteen`, `ninety_nine` | | | Non-squares; `fifteen` and `ninety_nine` are just below a square |
| `million`, `million_minus_one` | 10^6, 10^6 − 1 | 1000, 999 | T2 starts failing here |
| `big_non_square` | 123456789 | 11111 | Large interior answer |
| `square_46339` | 46339² | 46339 | Largest square below the top answer |
| `below_top_square` | 46340² − 1 | 46339 | Largest x whose answer is 46339 |
| `top_square` | 46340² | 46340 | B2, and Q1 at the top |
| `int_max` | 2^31 − 1 | 46340 | B2, non-square |

**Probes.** These are modelling assumptions:

| Probe | Skills | Tests |
| --- | --- | --- |
| `zero_input` | boundaries | `zero` |
| `one_input` | boundaries, termination | `one` |
| `perfect_square` | equality | `four`, `nine`, `sixteen`, `hundred`, `million`, `square_46339`, `top_square` |
| `non_square` | specification | every other test except `zero` and `one` |
| `small_value` | termination | x ≤ 16 |
| `large_value` | termination | x ≥ 10^6 |
| `top_of_range` | boundaries | `top_square`, `int_max` |

**Harness input.** A single integer, validated as `0 <= x <= 2^31 − 1` (exit 64 otherwise).
One call per test.

## 4. Discrimination

### 4.1 Predicted (design time, Python re-implementation; not a measurement)

Simulation script: `scratchpad/g2/sim.py`, not committed. `·` means the same as the
reference. TLE is a predicted time limit.

| Test | Ref | `hi_excludes_x` | `hi_cap_46340` | `closed_loop_lt` | `floor_mid_no_progress` | `fixed_iterations_16` | `strict_square_test` | `returns_ceiling` | `returns_lo_closed` |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| `zero` | 0 | -1 | · | · | · | · | · | · | 1 |
| `one` | 1 | 0 | · | 0 | TLE | · | 0 | · | 2 |
| `two` | 1 | · | · | · | TLE | · | · | 2 | 2 |
| `three` | 1 | · | · | · | · | · | · | 2 | 2 |
| `four` | 2 | · | · | · | · | · | 1 | · | 3 |
| `eight` | 2 | · | · | · | TLE | · | · | 3 | 3 |
| `nine` | 3 | · | · | 2 | TLE | · | 2 | · | 4 |
| `ten` | 3 | · | · | · | TLE | · | · | 4 | 4 |
| `fifteen` | 3 | · | · | · | · | · | · | 4 | 4 |
| `sixteen` | 4 | · | · | 3 | TLE | · | 3 | · | 5 |
| `ninety_nine` | 9 | · | · | · | TLE | · | · | 10 | 10 |
| `hundred` | 10 | · | · | 9 | TLE | · | 9 | · | 11 |
| `million` | 1000 | · | · | 999 | TLE | 990 | 999 | · | 1001 |
| `million_minus_one` | 999 | · | · | · | TLE | 990 | · | 1000 | 1000 |
| `big_non_square` | 11111 | · | · | 11110 | TLE | 9417 | · | 11112 | 11112 |
| `top_square` | 46340 | · | 46339 | · | TLE | 32765 | 46339 | · | 46341 |
| `below_top_square` | 46339 | · | · | 46338 | TLE | 32765 | · | 46340 | 46340 |
| `int_max` | 46340 | · | 46339 | 46339 | TLE | 32767 | · | 46341 | 46341 |
| `square_46339` | 46339 | · | · | 46338 | · | 32764 | 46338 | · | 46340 |

**Predicted support.**

| Model | Tests | Behaviour groups |
| --- | --- | --- |
| `hi_excludes_x` | 2 | 2 |
| `hi_cap_46340` | 2 | 2 |
| `closed_loop_lt` | 9 | 6 |
| `floor_mid_no_progress` | 14 | 8 |
| `fixed_iterations_16` | 7 | 6 |
| `strict_square_test` | 8 | 6 |
| `returns_ceiling` | 10 | 5 |
| `returns_lo_closed` | 19 | 12 |

- There are 12 groups in all.
- Every pair is separated by at least 4 tests.
- Two termination models (T1, T2) are predicted to fail with **wrong outputs, not time
  limits**. This is the CE1.2 target for gap 4.

### 4.2 Measured (2026-10-24)

Content written and measured on 2026-10-24, in the sandbox (`runc`, image
`codeadapt-sandbox:gcc14.2-1`, 2 runs per test). Report:
[`docs/content-reports/integer-sqrt.md`](../content-reports/integer-sqrt.md); validation result:
valid, 0 errors, 0 warnings.

- **The measured matrix is identical to the prediction in §4.1**, cell for cell, with
  `time_limit` where §4.1 says TLE.
- Detecting tests and behaviour groups per model match the predicted support table.
- B1 (`hi_excludes_x`) and B2 (`hi_cap_46340`) each span 2 behaviour groups, so under the rule
  in §4.3 neither gets a `known_limitation`. §4.3's caution still applies: each rests on 2
  tests, and its second group exists only because another model splits the pair.
- The 8 held-out cases (§7) were committed in a separate commit after this content and before
  `codeadapt-eval` was run on them.

### 4.3 Ambiguity analysis (before measurement)

- **B1 and B2 rest on 2 tests each.**
  - Their second group comes only from another model splitting the pair: S2 for B1's
    `zero`/`one`, Q1 for B2's `top_square`/`int_max`. Any unmodelled error that fails
    exactly those inputs with the same outputs would be diagnosed as B1 or B2.
  - Example for B2: a result clamped to 46339.
  - If measurement leaves either with one group, it gets a `known_limitation` and its
    diagnoses become qualified, not skill evidence.
- **T1 against Q1.** Both are one too small on several perfect squares. The prediction
  separates them on `four`, `big_non_square`, `top_square`, `below_top_square` and
  `int_max`. If measurement shows them inseparable, the diagnosis must report them as
  ambiguous, not pick one.
- **S1 and S2** agree on every non-square and differ on every square: they are separable.
- **T3** is seen only as time limits, as in the other problems.
- **U2 (unsigned wrap)** gives wrong large-x outputs that could resemble T2's. The
  prediction for T2's outputs is specific (for example 32765 on `top_square`), so a
  collision is unlikely. The held-out U2 case checks this.

### 4.4 Errors the suite cannot see

- A linear scan.
- Floating-point `sqrt`, which is exact for every integer up to 2^31 in `double`.
- U1 (signed overflow), when the optimiser happens to produce the right answer.

## 5. From evidence to concepts

| Observed | Hypothesis | Skill | Next activity (the record's intent; policy v1 does not act on it) |
| --- | --- | --- | --- |
| One too small on perfect squares only | Q1 | equality | lower-bound (equality tests) |
| Wrong (too small) on scattered inputs, terminating | T1 | termination | first-true (`stops_one_early` contrast) |
| Wrong only for large x, terminating | T2 | termination | the record's own explanation: the range is `[0, x]`, not `[0, 46340]` |
| Time limits | T3 | termination | lower-bound or first-true (`no_progress_update`) |
| Wrong for x = 0 and 1 only | B1 | boundaries | first-true (`empty`, `answer_none`) |
| 46339 at the top only | B2 | boundaries | lower-bound (`above_all`) |
| One too large on non-squares | S1 | specification | last-less-than (reading which side of the boundary to return) |
| Always one too large | S2 | specification | last-less-than |
| Abstention | unmodelled | none claimed | retry; flagged for review |

## 6. Follow-up and curriculum links

- **Role.** A search-over-answers step after the array problems, and before G3, which is
  a transfer problem.
- **`[curriculum]` links.**
  - `prerequisites = ["first-true", "lower-bound"]`.
  - `assumes` names `long long` and integer overflow.
  - No reverse links are added: those would change existing content versions.
- **Recommendation behaviour (decision E2).** `recommendable = false`.
  - Policy v1.3 never recommends integer-sqrt.
  - It stays in the problem list, and its attempts feed skill evidence and the
    researcher-only learner model.
  - The policy golden test must still pass unchanged.
- **Follow-up criterion.** This is the family rule.

## 7. Held-out plan and known limitations

**Held-out plan.** There will be 8 cases:
- 2 correct, in different styles: a division test `mid <= x / mid`, and integer Newton
  iteration.
- 4 modelled, in a style different from the models: T1, Q1, S1 and B2.
- 2 unmodelled: an `unsigned` 32-bit wrap (U2), and a double error.

They are written and committed after the content and before `codeadapt-eval` runs on them.
They live in `eval/heldout/integer-sqrt/`. No calibration cases are planned.

**Known limitations, before measurement.**
- B1 and B2 rest on 2 tests each.
- T3 is visible only as time limits.
- Overflow errors are not modelled; that is a possible taxonomy gap, not addressed here.
- O(log x) and the ban on `sqrt` are not enforced.
- The held-out cases are written by the models' author.
