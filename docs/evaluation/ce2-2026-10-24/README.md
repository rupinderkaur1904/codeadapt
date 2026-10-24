# CE2 held-out evaluations (2026-10-24)

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

## Results, per problem (kept separate)

- **upper-bound.** All 3 modelled cases were named correctly, both unmodelled cases were
  abstained on, and there were 0 false alarms on 2 correct programs.
- **exact-search.** The results were the same: 3 of 3 modelled cases named correctly, 2 of 2
  unmodelled cases abstained on, and 0 false alarms on 2 correct programs.
- **Both problems.** All cases were reproducible across 2 runs, and v1.1, v1.2 and v1.3 gave
  identical outcomes on every case.

**Not covered.** No termination model (`no_progress_update`, `closed_loop_hi_mid`) appears as a
held-out truth. The measured behaviour of those models is in each problem's content report.
