# Proposed lower-bound changes (not committed content)

These files back proposals C1–C3 in [../../lower-bound.md](../../lower-bound.md) §7. They
were measured in a scratch copy of the problem with `codeadapt-content validate`. They are
kept here, outside `content/`, so the catalogue never loads them: nothing in this folder
is served, fingerprinted for students or used by a diagnosis.

Applying C1 and C2 needs the owner's decision, because it changes the content version.

| File | Proposal | Measured status |
| --- | --- | --- |
| `hi_skips_candidate.cpp` | C2, model E6 (`search_space_boundaries`) | deterministic, UB-free, separable from every model |
| `closed_loop_hi_mid.cpp` | C2, model E7 (`loop_termination`) | deterministic, UB-free, separable from every model |
| `returns_wrong_pointer.cpp` | C2, model E8 (`problem_specification`) | deterministic, UB-free, separable from every model |
| `closed_loop_reads_past_end.cpp` | C3, rejected (E9) | undefined behaviour: sanitizer reports `heap-buffer-overflow` |
| `linear_scan.cpp` | C3, rejected (E10) | undetectable: identical to the reference on every test |

Proposed tests (C1), in `problem.toml` syntax:

```toml
[[tests]]
key = "pair_equal_target"
input = "L 2 5 5 5"
expected = "0"
probes = ["target_present_duplicates", "two_elements"]

[[tests]]
key = "absent_after_duplicates"
input = "L 6 1 2 2 4 4 5 3"
expected = "3"
probes = ["target_absent_between"]
```

Their `student_description`, `purpose` and `distinguishes` would be written when the
proposal is applied, and `distinguishes` would be checked by validation.
