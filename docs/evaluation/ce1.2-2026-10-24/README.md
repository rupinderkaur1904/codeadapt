# CE1.2 held-out evaluation: integer-sqrt (2026-10-24)

**Synthetic, author-written cases.** Not an accuracy estimate for real students.

- **Order.** Content in 2beff5e; held-out cases in 116922a, committed before this run.
- **Command** (from `backend/`):

  ```
  uv run codeadapt-eval --content ../content/demo --heldout ../eval/heldout \
    --problem integer-sqrt --runs 2 --compare v1.1 v1.2 v1 \
    --json ../docs/evaluation/ce1.2-2026-10-24/heldout.json \
    --markdown ../docs/evaluation/ce1.2-2026-10-24/heldout.md
  ```

- **Environment.** g++ 14.2.0, `runc`, image `codeadapt-sandbox:gcc14.2-1`, 2 runs per case.

| Case | Truth | v1.3 outcome | Named |
| --- | --- | --- | --- |
| `division_test.cpp` | correct | no_failure_observed | — |
| `newton_integer.cpp` | correct | no_failure_observed | — |
| `for_loop_last_unchecked.cpp` | `closed_loop_lt` | hypothesis_supported | `closed_loop_lt` |
| `too_big_branch_first.cpp` | `strict_square_test` | hypothesis_supported | `strict_square_test` |
| `smallest_square_at_least.cpp` | `returns_ceiling` | hypothesis_supported | `returns_ceiling` |
| `capped_closed_range.cpp` | `hi_cap_46340` | hypothesis_supported | `hi_cap_46340` |
| `unsigned_wrap.cpp` | unmodelled | unmodelled_behaviour | — |
| `strict_and_capped.cpp` | unmodelled | unmodelled_behaviour | — |

**Results.**

- Coverage of buggy cases is 4/6. All 4 names are correct, and both unmodelled cases are
  abstained on.
- There are 0 false alarms on correct programs, and all 8 cases are reproducible across 2 runs.
- v1.1, v1.2 and v1.3 give identical outcomes on every case.

**Limits.**

- 8 cases is too few for rates.
- The modelled cases were written by the models' author to contain one modelled error each,
  so naming them is the expected minimum, not evidence of real-world precision.
- No modelled termination case (T2, T3) and no boundary case B1 is in the held-out set.
