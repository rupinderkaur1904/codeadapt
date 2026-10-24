# Content design record: `rotated-min` (BSX, binary-search extension)

**Label.** Files and commits call this "CE2". That was a working label; this is a binary-search family extension, not the planned CE2 stage (arrays).

**Status and order.**

- Written on 2026-10-24 together with the content, during the overnight bank expansion.
- The matrix was predicted by native runs (a scratch tool, not committed), then measured in the
  sandbox. The measurement is authoritative: [content report](../content-reports/rotated-min.md).
- The held-out cases were committed after the content and before `codeadapt-eval` ran on them.

## 1. Learning objective

Binary search on a property that is **not** a comparison with a target. The test is "is
`a[mid]` larger than the last element of the range?", which splits a rotated sorted array into
a prefix where it holds and a suffix where it does not. The answer is the first index of that
suffix.

**Contract.**

```cpp
int rotated_min_index(const std::vector<int>& a);
```

- `a` is a rotation of a strictly increasing array, possibly not rotated at all.
- `1 <= n <= 200000`. The harness checks the rotation property and the size.
- Return the index of the smallest element.
- Asks for O(log n) and forbids `std::min_element`. Neither rule is enforced (§4).

**Skills.** Three of the four existing keys. `equality_handling` is not listed:

- with distinct values and `mid < hi`, `a[mid] == a[hi]` cannot happen;
- so no equality error is observable here.

No new skill is proposed. The mapping of each model to a skill is a modelling assumption.

**Flag for review.** `compares_with_lo` is mapped to `search_space_boundaries`:

- its effect is that the update discards the half containing the minimum;
- its cause is choosing the wrong reference element;
- that cause is not described by any of the four skills.

This is noted as evidence for the owner, not acted on (CE1 rule: no new skill without
approval).

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `compares_with_lo` | search_space_boundaries | Tests `a[mid] >= a[lo]`, which fails when the range is not rotated |
| `hi_skips_candidate` | search_space_boundaries | `hi = mid - 1`, which can discard the minimum itself |
| `no_progress_update` | loop_termination | `lo = mid`, so the range stops shrinking (time limit) |
| `returns_value` | problem_specification | Returns `a[lo]` instead of `lo` |
| `returns_pivot` | problem_specification | Returns the index of the maximum: `(lo - 1) mod n` |

**Not modelled.**

- `while (lo <= hi)` with `hi = mid` (non-termination). It is time-limit-only, like
  `no_progress_update`, and never named under v1.3 (ADR-027).
- A linear scan for the minimum. This is correct and passes.
- Two errors at once.

## 3. Tests

There are 18 tests:

- 2 samples: rotated, and not rotated;
- a single element;
- pairs, both rotated and not;
- the minimum last, second, fourth or fifth, or in the middle;
- small arrays of 3, a long unrotated array, and negative values;
- four large tests (200,000 elements): not rotated, rotated by half, the minimum last, and the
  minimum second.

Values are chosen so that no value equals the expected index, so `returns_value` cannot pass by
coincidence.

## 4. Measured discrimination and ambiguity

The sandbox validation result is `ok`, with one documented limitation.

**`hi_skips_candidate` has a single behaviour group.**

- Its 4 detecting tests are all rotated arrays whose minimum becomes a midpoint.
- On those tests `no_progress_update`, `returns_pivot` and `returns_value` also fail.
- A brute-force search over every rotation of `n = 4..11` found no input on which both
  `hi_skips_candidate` and `compares_with_lo` fail. So a second group cannot be built from
  this model set.
- Its outputs differ from the others' on those tests. It carries a `known_limitation`, and its
  diagnoses are reported as qualified.

**Collision on unrotated input.**

- `compares_with_lo` and `returns_pivot` both output `n - 1` when the input is not rotated.
- They separate on rotated tests: `compares_with_lo` passes `min_last`, and `returns_pivot`
  fails it.

**Other limits.**

- `no_progress_update` is seen only as time limits and is never named under v1.3.
- O(log n) is not assessed, and a linear scan passes.

## 5. Role in the bank and recommendation

- `recommendable = false` (decision E2). Policy 1.4 and its golden test are unchanged.
- Attempts are diagnosed and produce skill evidence for the researcher-only learner model.
- `prerequisites = ["first-true", "lower-bound"]`.

## 6. Held-out plan

There are 8 cases in `eval/heldout/rotated-min/`, all written by the models' author:

- 2 correct;
- 4 modelled in different styles;
- 2 unmodelled.
