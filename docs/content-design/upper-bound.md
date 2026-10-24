# Content design record: `upper-bound` (BSX, binary-search extension)

**Label.** Files and commits call this "CE2". That was a working label; this is a binary-search family extension, not the planned CE2 stage (arrays).

**Status and order.**

- Written on 2026-10-24 together with the content. Unlike CE1.1 and CE1.2, there is no separate
  pre-measurement commit: the owner asked for bank expansion overnight.
- The matrix was predicted by native runs (a scratch tool, not committed), then measured in the
  sandbox. The measurement is authoritative: [content report](../content-reports/upper-bound.md).
- The held-out cases were committed after the content and before `codeadapt-eval` ran on them.

## 1. Learning objective

Find the first element strictly greater than a target in a sorted array with duplicates. It is
the strict counterpart of lower-bound: the only change is which side elements equal to the
target belong to.

**Contract.**

```cpp
int upper_bound_index(const std::vector<int>& a, int target);
```

- `a` is non-decreasing and may be empty or contain repeats.
- Return the smallest `i` with `a[i] > target`, or `a.size()` if there is none.
- Asks for O(log n) and forbids the library searches. Neither rule is enforced (§4).

**Skills.** The four existing keys; no new skill is proposed.

**Not a duplicate.**

- lower-bound uses `>=`; this problem uses `>`.
- count-occurrences uses an upper bound internally, but asks for a count. Here the index itself
  is the answer, including `a.size()`.

## 2. Error models

| Model | Skill | Error |
| --- | --- | --- |
| `lower_bound_confusion` | equality_handling | `a[mid] < target` moves right, which returns the lower bound |
| `hi_init_last_index` | search_space_boundaries | `hi = n - 1` with a half-open loop, so `n` is unreachable |
| `hi_skips_candidate` | search_space_boundaries | `hi = mid - 1` in a half-open loop, which drops mid |
| `no_progress_update` | loop_termination | `lo = mid`, so the range stops shrinking (time limit) |
| `closed_loop_hi_mid` | loop_termination | `lo <= hi` with `hi = mid`, so the loop never ends (time limit) |
| `returns_last_not_greater` | problem_specification | Returns `lo - 1`: the last element `<= target` |
| `none_sentinel` | problem_specification | Returns -1 instead of `a.size()` |

**Not modelled.**

- Early return on a greater element.
- Two errors at once.
- Linear scans and `std::upper_bound`. These are correct and produce identical output.

## 3. Tests

There are 19 tests:

- 2 samples: duplicates, and an absent target;
- empty, below all, above all;
- a target equal to the first or last element;
- duplicates in the middle, all equal, all equal and greater;
- single elements and pairs;
- four large tests (200,000 elements).

Probes and skills follow lower-bound's mapping (a modelling assumption).

## 4. Measured discrimination and ambiguity

See the content report.

**Known risks.**

- `hi_init_last_index` and `none_sentinel` both fail exactly the tests whose answer is `n`.
  They differ in output (`n - 1` against -1), so they separate on every such test.
- Any other error that cannot return `n` (for example, clamping to `n - 1`) would match
  `hi_init_last_index`'s outputs. This is the same collision documented for first-true.
- The two termination models are seen only as time limits. Under v1.3 they are never named
  (ADR-027).
- O(log n) is not assessed, and a linear scan passes.

## 5. Role in the bank and recommendation

- `recommendable = false` (decision E2 applied to every new problem). The policy never picks it,
  and policy 1.4 and its golden test are unchanged.
- Attempts are diagnosed and produce skill evidence for the researcher-only learner model.
- `prerequisites = ["lower-bound"]`.

## 6. Held-out plan

There are 7 cases in `eval/heldout/upper-bound/`, all written by the models' author:

- 2 correct (a closed interval with a running answer, and power-of-two jumps);
- 3 modelled in different styles (`lower_bound_confusion`, `hi_skips_candidate`,
  `none_sentinel`);
- 2 unmodelled (two errors at once, and an early return).
