# L20 contestable cases #3 and #13: written analysis (2026-10-26)

**Status.** Analysis for the owner (request A.3, 2026-10-26).

**Nothing was changed.** Neither model received a `known_limitation`, and their mappings,
fingerprints and evidence are as before. Both still give an `incorrect` observation when
named unqualified (pinned by `test_the_contestable_cases_are_not_changed` in
backend/tests/unit/test_l20_safeguards.py).

**Source of the cases.** docs/reviews/2026-10-25/l20-search.md, §3.1 cases 3 and 13. The raw
output is in l20-search/results.txt.

## Shared background

In both cases the model and the alternative compute the same function. On every committed
test, every exhaustive-domain input and every random-domain input they give the same output,
and a one-line argument makes the equivalence exact on the whole valid domain. **No test can
separate them.**

So the question is not empirical. It is whether the alternative's cause belongs to a
**different skill** from the one the model is mapped to. Only then is the attribution not
unique.

The four binary-search skill definitions (content/taxonomy.py, unchanged by ADR-034):

| Skill | Definition |
| --- | --- |
| `search_space_boundaries` | Initialising and updating the bounds of the search space so every candidate answer stays reachable. |
| `loop_termination` | Ensuring each iteration shrinks the search space so the loop terminates. |
| `equality_handling` | Choosing the comparison so equal elements land on the correct side of the boundary. |
| `problem_specification` | Returning what the specification asks for, including when the target is absent. |

Both models fail every committed test, because they are wrong on every input. Each spans
several behaviour groups (8 and 12, docs/content-reports/), so v1.3 names them unqualified.

## Case #3: upper-bound `returns_last_not_greater`

### Contract and wording

The statement (content/demo/upper-bound/statement.md) says:

> Implement `int upper_bound_index(const std::vector<int>& a, int target);`
>
> `a` is sorted in non-decreasing order and may be empty or contain repeated values. Return
> the smallest index `i` such that `a[i] > target` (strictly greater). If no such index
> exists, return `a.size()`.
>
> Your solution must run in O(log n) time. Do not call `std::lower_bound`,
> `std::upper_bound`, `std::equal_range` or `std::partition_point`.
>
> Examples: `a = [1, 3, 3, 5]`: `target = 3 → 3`; `target = 4 → 3`; `target = 5 → 4`;
> `target = 0 → 0`.

**The model** (`error_models/returns_last_not_greater.cpp`, skill `problem_specification`):
a correct half-open search for the boundary that returns `lo - 1`. That is the last index
whose element is `<= target`, or −1 when there is none. It is described as "Finds the
boundary but returns the index before it: the last element <= target." The student hint is
"Re-read which index to return: the first element greater than the target, not the last one
that is not."

### The alternative and its program

`docs/reviews/2026-10-25/l20-search/upper-bound/closed_returns_hi.cpp` is a correct
closed-interval loop that returns `hi` when the loop exits instead of `lo`:

```cpp
int lo = 0, hi = static_cast<int>(a.size()) - 1;
while (lo <= hi) {
    const int mid = lo + (hi - lo) / 2;
    if (a[mid] <= target) lo = mid + 1; else hi = mid - 1;
}
return hi;
```

On exit `hi = lo − 1`, and `lo` is the upper bound, so the program returns upper bound − 1,
exactly as the model does. The 2026-10-25 search labelled its cause `loop_termination`, and
marked it contestable.

### Evidence supporting the match (the mapping is right; no cross-skill twin)

- **The alternative's loop terminates correctly.** Every iteration shrinks the interval and
  the loop ends. `loop_termination` is defined as "ensuring each iteration shrinks the search
  space so the loop terminates", and nothing in that is wrong here. The error is the value
  returned after the loop.
- **The bank already classifies this cause as `problem_specification`.** lower-bound
  `returns_wrong_pointer` is "Correct closed-interval search that returns hi instead of lo".
  It is the same code pattern and has been mapped to `problem_specification` since the model
  was added (commit 777434f). Classifying `closed_returns_hi` differently would make the bank
  inconsistent with itself.
- **Every other program with this behaviour is a specification error too.**
  - The 2026-10-26 search of the original problems found the same structure several times:
    lower-bound O5, first-true O7, and the same-skill twins in its §2.4.
  - "Return the last element ≤ target" is a clean specification of a nearby task, the §4.2
    pattern. A student who misreads the task in that way writes a correct program with
    exactly this behaviour.
  - Both of these are `problem_specification` causes.
- **The hint fits both programs.** "Re-read which index to return" is correct advice for the
  model and for the alternative.

### Evidence challenging the match

- **The alternative's author did not misread the task.** They knew the answer was "first >"
  and reasoned wrongly about which variable holds it at exit. One can argue that this is
  reasoning about the loop's end state, and so belongs with the loop (`loop_termination`) or
  with the invariant on the bounds (`search_space_boundaries`), not with the specification.
- **The `problem_specification` definition is about content.** It speaks of "returning what
  the specification asks for", that is, which answer is wanted. A mistake about which
  variable holds the answer is a different mental error, even if it has the same observable
  effect.
- **The classification is mine.** No second reviewer has checked it.

### Recommended disposition: keep as is

- No `known_limitation`.
- The mapping to `problem_specification` stays.
- The case is reclassified as a **same-skill** equivalence.

**Rationale:**

- The challenging reading puts "which end to return" outside `problem_specification`. That
  contradicts how the bank already maps the identical cause in lower-bound.
- The alternative's loop is not a termination error under the skill's own definition.

**What would change this.** If the owner or a second reviewer decides that "which variable
to return at exit" is not a specification error, the decision should be made once, for every
model of this kind. These are:

- upper-bound `returns_last_not_greater`;
- lower-bound `returns_wrong_pointer`;
- first-true `returns_last_false`;
- integer-sqrt `returns_lo_closed`;
- last-less-than `returns_insertion_point`.

Patching #3 alone would leave the others inconsistent.

## Case #13: integer-sqrt `returns_lo_closed`

### Contract and wording

The statement (content/demo/integer-sqrt/statement.md) says:

> Implement `int int_sqrt(int x);`
>
> `0 <= x <= 2^31 - 1`. Return the integer square root of `x`: the largest `r` with
> `r * r <= x` (that is, `floor(sqrt(x))`, which is at most 46340).
>
> Compute `r * r` in 64-bit arithmetic (`long long`): `46341 * 46341` does not fit in an
> `int`.
>
> Your solution must run in O(log x) time. Do not call `sqrt`, `sqrtf`, `sqrtl`, `pow`,
> `cbrt` or `hypot`.
>
> Examples: `x = 8 → 2`; `x = 16 → 4`; `x = 0 → 0`.

**The model** (`error_models/returns_lo_closed.cpp`, skill `problem_specification`):

- a closed-interval search over [0, x] with no running answer;
- `if (mid * mid <= x) lo = mid + 1; else hi = mid - 1;`
- returns `lo`, which ends one past the answer: ⌊√x⌋ + 1 on every input.

Its description reads "Closed interval with no running answer, returning lo, which ends one
past the answer on every input." The student hint is "When your loop ends, which variable
holds the largest r with r * r <= x?"

### The alternative and its program

`docs/reviews/2026-10-25/l20-search/integer-sqrt/answer_records_next.cpp` is a closed
interval with a running answer that records `mid + 1` instead of `mid`:

```cpp
long long lo = 0, hi = x, ans = 0;
while (lo <= hi) {
    const long long mid = lo + (hi - lo) / 2;
    if (mid * mid <= x) { ans = mid + 1; lo = mid + 1; } else hi = mid - 1;
}
return static_cast<int>(ans);
```

The last `mid` with `mid * mid <= x` is ⌊√x⌋, so the program returns ⌊√x⌋ + 1, exactly as
the model does. The 2026-10-25 search labelled its cause "loop_termination / update rule
(not a declared skill here)".

### Evidence supporting the match (the mapping is right; no cross-skill twin)

- **No declared skill fits the alternative better.**
  - It is not `loop_termination`: the loop shrinks and ends correctly.
  - It is not `search_space_boundaries`: the bounds `lo` and `hi` are initialised and
    updated correctly, and every candidate stays reachable. `ans` is not a bound of the
    search space.
  - It is not `equality_handling`: the comparison `mid * mid <= x` is correct.
  - What is wrong is the value recorded as the answer, that is, what the program returns.
    Of the four definitions, only "returning what the specification asks for" describes it.
- **The behaviour is a clean specification of a nearby task.** ⌊√x⌋ + 1 is "the smallest r
  with r * r > x". A student who reads the task as "first r whose square exceeds x" writes a
  correct program for that reading, and it is a `problem_specification` cause. The same
  pattern appears in last-less-than O6 and first-true O7 (l20-search-original.md).
- **The bank maps the analogous end-of-search cause to `problem_specification`.** lower-bound
  `returns_wrong_pointer` and the model itself are examples, consistent with case #3.

### Evidence challenging the match

- **"Update rule" is a reasonable description** of recording mid + 1. Under the old
  `update_rule` key (non-binary-search families, retired by ADR-034) that is how it would
  have been described. In the new taxonomy it is closest to `running_state`, "keeping a
  tracked value current on every step". Neither key is declared for integer-sqrt, and
  neither is defined for binary search.
- **The alternative's author did not misread the task.** As in #3, they knew what to return
  and made a mechanical slip, and the mapped skill names the misreading.
- **The 2026-10-25 label leaves it open.** Its author (me) did not assign the cause to a
  declared skill. An undeclared-skill twin means the observation still lands on a declared
  skill (`problem_specification`) that may not be the cause.

### Recommended disposition: keep as is, with lower confidence than #3

- No `known_limitation`.
- The mapping stays.
- The case is recorded as having no cross-skill twin among the **declared** skills.

**Rationale:**

- Under the current definitions, the alternative's cause falls under
  `problem_specification` or under no declared skill at all.
- The misreading program ("smallest r with r * r > x") is an exact same-skill twin.
- Applying a `known_limitation` here but not to the analogous models listed under #3 would
  be inconsistent.

**Conservative option, if the owner prefers it.** Add a `known_limitation` to
`returns_lo_closed`, following the S1 route. That would withhold its `incorrect` observations
and change nothing else; integer-sqrt's `problem_specification` would keep negative evidence
through `returns_ceiling`. It is a policy choice about undeclared-skill
causes, not something the evidence settles. If it is taken, it should apply to the
end-of-search family of models named under #3, not to #13 alone.

## Decisions still open

1. **Is "which variable to return or record at the end" a `problem_specification` error?**
   The recommendation is yes, consistent with lower-bound `returns_wrong_pointer`. A no would
   affect five models, and should be decided once for all of them.
2. **May an undeclared-skill cause count as a cross-skill twin?** This applies to #13, and
   to l20-search.md case #10, where S1 treated it as one. The recommendation is to keep #13
   as is, but #10's precedent makes this a genuine owner choice.
3. **A second reviewer** for the cause classifications in both searches would reduce the
   reliance on my judgement.
