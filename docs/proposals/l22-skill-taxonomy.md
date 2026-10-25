# Proposal L22: a revised taxonomy for the new families' skill keys

**Status.** Design proposal for owner review (owner action 5, 2026-10-25). **Nothing here is
implemented.** The skill keys (ADR-033), the mappings, the content versions and the BKT
parameters are unchanged.

**Problem.** L22 and docs/reviews/2026-10-25/expansion-audit.md §4. The learner model pools
observations by skill key across every problem and family. Two of the five ADR-033 keys,
`update_rule` and `index_range`, each join mechanisms that have no shared reason to transfer.
A result on carry propagation then moves the estimate for removing a window's leaving element.

## 1. Principles

1. **Name what the tests can observe.** The L20 search
   (docs/reviews/2026-10-25/l20-search.md) shows that functional tests identify an
   input–output behaviour, not the cause in the student's head. A key should name a class of
   behaviour, such as "a window keeps an element that has left it", not a misconception. This
   is already ADR-033's definition rationale; the proposal applies it more strictly.
2. **Pool only where transfer is plausible.** That means the same mechanism, not the same
   kind of word. Prefer a narrower key with less evidence over a broad key whose evidence is
   mixed. Fewer observations per key is the honest cost: estimates appear later, at the same
   display threshold (3 observations from 2 problems).
3. **Every declared skill has at least one model.** A skill with probing tests but no model
   can only gain `correct` evidence through rule C (L19). pivot-index `index_range` is the
   current case.
4. **No key splits on one problem alone.** A key used by one problem cannot cross the
   display threshold. Problem-specific behaviour stays under the nearest shared key.

## 2. Proposed keys

The current keys are on the left and the proposed keys on the right. Model lists use the
audit's mapping table. `*` marks a documented collision (`known_limitation`), which gives no
`incorrect` evidence.

### 2.1 `update_rule` splits into three

| Proposed key | Observable behaviour | Models | Problems (families) |
| --- | --- | --- | --- |
| `window_maintenance` | The window's state is not updated when an element leaves, or is reset instead of shrunk | max-window-sum: never_subtracts, subtracts_wrong_element; distinct-in-windows: keeps_zero_counts; longest-sum-at-most: restarts_window | 3 (sliding-window) |
| `pointer_movement` | The wrong pointer moves, or a pointer moves without the write it guards | closest-pair-sum: moves_wrong_pointer; container-water: moves_taller*; dedup-sorted: compares_to_first, counts_without_writing | 3 (two-pointers) |
| `running_state` | A tracked value (second maximum, current run, carry, prefix sum) is not kept current, or not closed after the loop | second-largest: no_demotion; longest-run: last_run_unchecked, compares_to_first; plus-one: single_carry, carry_never_cleared; range-sum-queries: prefix_not_accumulated | 4 (arrays, prefix-sums) |

**pivot-index.** `pivot_counted_left` and `pivot_counted_right` include the pivot in a side
sum. They move to `range_inclusion` (§2.2), because what fails is which positions a sum
covers, not an update.

### 2.2 `index_range` splits into two

| Proposed key | Observable behaviour | Models | Problems (families) |
| --- | --- | --- | --- |
| `loop_bounds` | The loop visits one position too few or too many at either end | first-max-index: skips_last; second-largest: skips_first; stock-profit: misses_last_day; closest-pair-sum: skips_first; container-water: stops_before_adjacent; dedup-sorted: skips_last; max-window-sum: misses_last_window; distinct-in-windows: misses_last_window | 8 (arrays, two-pointers, sliding-window) |
| `range_inclusion` | A count or sum covers the wrong set of positions: interval length off by one, an end excluded, the pivot included, an element paired with itself | longest-sum-at-most: length_without_plus_one; container-water: width_plus_one; range-sum-queries: excludes_right_end; pivot-index: pivot_counted_left, pivot_counted_right; closest-pair-sum: allows_same_element | 5 (sliding-window, two-pointers, prefix-sums) |

**plus-one `adds_at_front`** (adds the carry at the wrong end) is not a range error. It reads
the digit order wrongly. It moves to `output_contract`, renamed `io_contract` (§2.4).

**pivot-index** then declares `range_inclusion` and has models for it. Principle 3 is met,
and the positive-only `index_range` evidence disappears.

### 2.3 `tie_resolution` splits into two

The audit flagged this key too (confound 3). It is smaller, and splitting it is optional.

| Proposed key | Observable behaviour | Models |
| --- | --- | --- |
| `tie_selection` | Among equal candidates, the wrong one wins | first-max-index: last_of_ties; pivot-index: last_pivot |
| `duplicate_counting` | Equal values are counted separately when they should not be, or not counted when they should | second-largest: counts_duplicates; distinct-in-windows: counts_unique_only |

Each has two problems from two families, so each can reach the display threshold.

### 2.4 Unchanged or renamed

- **`accumulator_init`.** Unchanged: one mechanism, three problems.
- **`output_contract` → `io_contract`.** Renamed only if `adds_at_front` moves in. Otherwise
  unchanged. Three problems probe it with only three tests (L22 confound 5). That is a
  test-coverage question, not a taxonomy one.

## 3. What this does and does not fix

**It fixes:**

- pooling of unrelated mechanisms under `update_rule` and `index_range`;
- the positive-only skill on pivot-index.

**It does not fix:**

- **L20 for the new families.** Cause-level attribution stays non-unique wherever an
  equivalent program exists. Narrower behavioural keys make the label more accurate, not the
  diagnosis more unique.
- **Validation.** Whether learners' errors cluster the proposed way is as untested as the
  current grouping. Only independent programs (deferred VAL1-B, or a permitted public
  corpus) could test it.
- **Binary search.** The four binary-search keys are named by cause (`equality_handling`,
  etc.), and the L20 search found cross-skill equivalences across most of them. A parallel
  revision is possible but is a separate decision. It touches the recommendable problems
  and the accepted CE1 record.

## 4. Effect if approved

**Content.**

- All 13 new-family problem.toml files change their `[skills]`, probe and model mappings,
  because every one of them uses `index_range` or `update_rule`.
- Each changed file gives a new content version, re-fingerprinting and re-evaluation.
- Earlier versions and their records stay (ADR-023 D4).

**Existing observations.**

- Not rewritten. Attempts keep the skill map snapshot of their content version, so observations
  recorded under `update_rule` stay under that key.
- **One decision is needed:** whether the learner-model view shows old-key and new-key
  evidence side by side, or filters to the current taxonomy.
- Only dev and test databases hold attempts.

**Recommendations.** No change. None of the new-family problems is recommendable (CE1 E2;
L21 wording applies).

**BKT.**

- Same assumed parameters (`bkt-params-assumed-1`) per key.
- More keys means fewer observations each, so more skills stay below the display threshold.
- No parameter change.

**ADR.** A new ADR superseding the key list of ADR-033, which keeps its record.

## 5. Questions for you

1. Split `update_rule` and `index_range` as in §2.1–2.2: yes, no, or a different grouping.
2. Split `tie_resolution` (§2.3), or leave it.
3. Move `adds_at_front` and rename `output_contract` (§2.4), or leave plus-one as it is.
4. How the learner-model view treats observations under retired keys.
5. Whether to consider a parallel review of the binary-search keys, in the light of the L20
   search.
