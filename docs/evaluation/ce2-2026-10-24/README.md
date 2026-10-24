# Binary-search extension (BSX) held-out evaluations (2026-10-24)

**Label note.** The 2026-10-24 binary-search additions carry the working label "CE2" in their commit messages, `problem.toml` comments, held-out manifests and this folder name. That label is a misnomer: they extend the **binary-search family** (call it BSX). They are not the planned CE2 stage (arrays and two pointers), which has not started. Content and held-out files are left unedited, because editing them would change content versions and held-out manifests after the fact.

**Synthetic, author-written cases.** These are not accuracy estimates for real students. The
error models and the held-out programs were written by the same author (Claude), so naming a
modelled case is the expected minimum, not evidence of real-world precision. 7 cases per problem
is too few for rates.

Each problem's content was committed first. Its held-out cases came in a separate, later commit
and were pushed before the evaluation ran.

| Problem | Content | Held-out cases |
| --- | --- | --- |
| `upper-bound` | a92ce36 | d35dcaf |
| `exact-search` | 701d15d | 052daf6 |
| `last-occurrence` | 41345d9 | 2070c41 |
| `min-capacity` (G3) | 6bb088e | 939baf0 |
| `rotated-min` | 1fee3a4 | 4f73f95 |
| `rotated-search` | a1d10e6 | c94e5a1 |

**Command** (from `backend/`; repeat for each problem):

```
uv run codeadapt-eval --content ../content/demo --heldout ../eval/heldout \
  --problem <slug> --runs 2 --compare v1.1 v1.2 v1 \
  --json ../docs/evaluation/ce2-2026-10-24/<slug>.json \
  --markdown ../docs/evaluation/ce2-2026-10-24/<slug>.md
```

**Environment.** g++ 14.2.0, `runc`, image `codeadapt-sandbox:gcc14.2-1`, 2 runs per case.

## upper-bound

| Case | Truth | v1.3 outcome | Named |
| --- | --- | --- | --- |
| `closed_interval_answer_var.cpp` | correct | no_failure_observed | — |
| `power_of_two_steps.cpp` | correct | no_failure_observed | — |
| `answer_starts_minus_one.cpp` | `none_sentinel` | hypothesis_supported | `none_sentinel` |
| `closed_answer_ge.cpp` | `lower_bound_confusion` | hypothesis_supported | `lower_bound_confusion` |
| `for_loop_right_drops_mid.cpp` | `hi_skips_candidate` | hypothesis_supported | `hi_skips_candidate` |
| `lower_bound_with_sentinel.cpp` | unmodelled | unmodelled_behaviour | — |
| `returns_any_greater.cpp` | unmodelled | unmodelled_behaviour | — |

## exact-search

| Case | Truth | v1.3 outcome | Named |
| --- | --- | --- | --- |
| `lower_bound_then_check.cpp` | correct | no_failure_observed | — |
| `recursive_closed.cpp` | correct | no_failure_observed | — |
| `for_loop_stops_early.cpp` | `closed_loop_lt` | hypothesis_supported | `closed_loop_lt` |
| `lower_bound_no_check.cpp` | `returns_insertion_point` | hypothesis_supported | `returns_insertion_point` |
| `recursive_from_one.cpp` | `lo_init_one` | hypothesis_supported | `lo_init_one` |
| `from_one_insertion_point.cpp` | unmodelled | unmodelled_behaviour | — |
| `one_based_index.cpp` | unmodelled | unmodelled_behaviour | — |

## last-occurrence

| Case | Truth | v1.3 outcome | Named |
| --- | --- | --- | --- |
| `closed_answer_variable.cpp` | correct | no_failure_observed | — |
| `power_of_two_jumps.cpp` | correct | no_failure_observed | — |
| `closed_goes_left_on_match.cpp` | `returns_first_occurrence` | hypothesis_supported | `returns_first_occurrence` |
| `for_loop_returns_on_match.cpp` | `stops_at_any_match` | hypothesis_supported | `stops_at_any_match` |
| `count_not_greater.cpp` | `returns_one_past` | hypothesis_supported | `returns_one_past` |
| `upper_midpoint_any_match.cpp` | `stops_at_any_match` | unmodelled_behaviour | — |
| `one_based_position.cpp` | unmodelled | unmodelled_behaviour | — |
| `unchecked_count.cpp` | unmodelled | unmodelled_behaviour | — |

## min-capacity (G3)

| Case | Truth | v1.3 outcome | Named |
| --- | --- | --- | --- |
| `closed_answer_variable.cpp` | correct | no_failure_observed | — |
| `count_style_search.cpp` | correct | no_failure_observed | — |
| `closed_from_one.cpp` | `lo_init_one` | hypothesis_supported | `lo_init_one` |
| `bool_check_strict.cpp` | `strict_day_limit` | hypothesis_supported | `strict_day_limit` |
| `segment_cut_at_full.cpp` | `full_day_overflows` | hypothesis_supported | `full_day_overflows` |
| `sorted_copy.cpp` | `sorts_weights` | hypothesis_supported | `sorts_weights` |
| `allows_one_over.cpp` | unmodelled | unmodelled_behaviour | — |
| `from_one_strict.cpp` | unmodelled | unmodelled_behaviour | — |

## rotated-min

| Case | Truth | v1.3 outcome | Named |
| --- | --- | --- | --- |
| `predicate_vs_last.cpp` | correct | no_failure_observed | — |
| `recursive_halves.cpp` | correct | no_failure_observed | — |
| `first_vs_mid.cpp` | `compares_with_lo` | hypothesis_supported | `compares_with_lo` |
| `smaller_than_end_skips.cpp` | `hi_skips_candidate` | hypothesis_supported | `hi_skips_candidate` |
| `returns_smallest_value.cpp` | `returns_value` | hypothesis_supported | `returns_value` |
| `returns_rotation_end.cpp` | `returns_pivot` | hypothesis_supported | `returns_pivot` |
| `one_based.cpp` | unmodelled | unmodelled_behaviour | — |
| `first_vs_mid_value.cpp` | unmodelled | unmodelled_behaviour | — |

## rotated-search

| Case | Truth | v1.3 outcome | Named |
| --- | --- | --- | --- |
| `min_then_search.cpp` | correct | no_failure_observed | — |
| `right_half_first.cpp` | correct | no_failure_observed | — |
| `left_sorted_strict_start.cpp` | `left_range_excludes_lo` | hypothesis_supported | `left_range_excludes_lo` |
| `for_loop_lt.cpp` | `closed_loop_lt` | hypothesis_supported | `closed_loop_lt` |
| `recursive_plain.cpp` | `ignores_rotation` | hypothesis_supported | `ignores_rotation` |
| `virtual_index.cpp` | `returns_sorted_position` | hypothesis_supported | `returns_sorted_position` |
| `one_based.cpp` | unmodelled | unmodelled_behaviour | — |
| `plain_lt_loop.cpp` | unmodelled | unmodelled_behaviour | — |

## Results, per problem (kept separate)

- **upper-bound.** All 3 modelled cases were named correctly, both unmodelled cases were
  abstained on, and there were 0 false alarms on 2 correct programs.
- **exact-search.** The results were the same: 3 of 3 modelled cases named correctly, 2 of 2
  unmodelled cases abstained on, and 0 false alarms on 2 correct programs.
- **last-occurrence.**
  - 3 of 4 modelled cases were named correctly.
  - The fourth, `stops_at_any_match` with the midpoint rounded up, was abstained on. The design
    record (§4) predicted this before the run.
  - Both unmodelled cases were abstained on, and there were 0 false alarms on 2 correct
    programs.
  - The miss is the known midpoint-convention limitation, also seen in first-true. It is a safe
    miss: no wrong name and no negative skill evidence.
- **min-capacity (G3).** All 4 modelled cases were named correctly, both unmodelled cases
  were abstained on, and there were 0 false alarms on 2 correct programs.
- **rotated-min.**
  - All 4 modelled cases were named correctly, both unmodelled cases were abstained on, and
    there were 0 false alarms on 2 correct programs.
  - `hi_skips_candidate` is a documented single-group model. v1.3 qualifies any diagnosis that
    rests on one behaviour (`evidence_strength = single_behaviour`), and a qualified diagnosis
    adds no negative skill evidence.
  - The evaluation output does not record the rationale, so qualification of this case is
    implied by the measured fingerprints, not observed here.
- **rotated-search.**
  - All 4 modelled cases were named correctly. One of them is `closed_loop_lt`, a termination
    error that shows as a wrong output, not a time limit.
  - Both unmodelled cases were abstained on, and there were 0 false alarms on 2 correct
    programs.
- **All six problems.** All cases were reproducible across 2 runs, and v1.1, v1.2 and v1.3 gave
  identical outcomes on every case.

**Not covered.** No time-limit-only termination model (`no_progress_update`,
`closed_loop_hi_mid`) appears as a held-out truth; under v1.3 they would never be named. The measured behaviour of those models is in each problem's content report.
