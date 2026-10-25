# Bank expansion held-out evaluations (2026-10-25)

**What these are.** For each of the 13 new problems, synthetic held-out programs written by
the error models' author, in styles different from the models, committed before the method was
run on them (`eval/heldout/<slug>/`). They test that the fingerprint method names modelled
mistakes written in other ways and abstains on mistakes it does not model. They are **not**
evidence of diagnostic accuracy on real students' code (see docs/methodology.md §6.1): the same
person wrote the models, the tests and the cases.

**Command** (one problem; from `backend/`, Docker sandbox, runc):

```
uv run codeadapt-eval --content ../content/demo --heldout ../eval/heldout --problem <slug> \
    --runs 2 --compare v1.1 v1.2 v1 \
    --json ../docs/evaluation/expansion-2026-10-25/<slug>.json \
    --markdown ../docs/evaluation/expansion-2026-10-25/<slug>.md
```

## Results under method v1.3 (v1.1 and v1.2 gave identical outcomes on every case)

| Problem | Family | Cases | Correct programs | Buggy | Named (all correct) | Wrong name | Abstained | False alarms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first-max-index | arrays | 8 | 2 | 6 | 4 | 0 | 2 | 0 |
| second-largest (v1, first run) | arrays | 8 | 2 | 6 | 4 | **1** | 1 | 0 |
| second-largest (v2) | arrays | 8 | 2 | 6 | 4 | 0 | 2 | 0 |
| stock-profit | arrays | 7 | 2 | 5 | 3 | 0 | 2 | 0 |
| longest-run | arrays | 8 | 2 | 6 | 4 | 0 | 2 | 0 |
| plus-one | arrays | 8 | 2 | 6 | 4 | 0 | 2 | 0 |
| closest-pair-sum | two-pointers | 8 | 2 | 6 | 4 | 0 | 2 | 0 |
| container-water | two-pointers | 8 | 2 | 6 | 4 | 0 | 2 | 0 |
| dedup-sorted | two-pointers | 8 | 2 | 6 | 4 | 0 | 2 | 0 |
| max-window-sum | sliding-window | 8 | 2 | 6 | 4 | 0 | 2 | 0 |
| longest-sum-at-most | sliding-window | 7 | 2 | 5 | 3 | 0 | 2 | 0 |
| distinct-in-windows | sliding-window | 7 | 2 | 5 | 3 | 0 | 2 | 0 |
| pivot-index | prefix-sums | 8 | 2 | 6 | 4 | 0 | 2 | 0 |
| range-sum-queries | prefix-sums | 7 | 2 | 5 | 3 | 0 | 2 | 0 |

**Totals (current versions, second-largest v2):** 100 cases; 26 correct programs, 0 false
alarms; 48 modelled cases, all named correctly; 26 unmodelled cases, all abstained. Every
abstention is `unmodelled_behaviour`.

**The one wrong name, and what was done.** On the first run, second-largest's
`after_max_only.cpp` (unmodelled: looks for the answer only after the maximum's position) was
named `no_demotion`. The design record had claimed that a test separated them; it did not.
Test `answer_before_max` was added (content version v2) and the case now abstains. Because the
fix was made after seeing the case, the v2 result for that case is **not** an independent check;
the v1 result stays recorded in `second-largest.{json,md}`.

**Reading these numbers.** "Named, all correct" means the method named the model the author
labelled. Three of the named models carry a documented non-unique attribution
(`stock-profit/ignores_order`, `container-water/moves_taller`, `dedup-sorted/returns_last_index`;
ADR-032 route): their diagnoses are shown qualified and add no skill evidence. See
[STATUS.md](STATUS.md) for each problem's completion levels.
