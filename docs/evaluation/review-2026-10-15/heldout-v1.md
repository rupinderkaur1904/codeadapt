# CodeAdapt synthetic evaluation report

Method `fingerprint_consistency` v1.1; case set `heldout`; data class `synthetic`; each case run 2 times; g++ (GCC) 14.2.0 on `runc`.

## Overall

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 17 (13 / 4) |
| Coverage (buggy cases diagnosed) | 9/13 (69%) |
| Selective accuracy (diagnoses matching truth) | 9/9 (100%) |
| False-positive diagnoses | 0 |
| False negatives (modelled bugs not diagnosed) | 0/9 (0%) |
| Correct code with no failure observed | 4/4 (100%) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 4 |
| Reproducible across 2 runs | 17/17 (100%) |

## count-occurrences (content d1b043c04574)

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 5 (4 / 1) |
| Coverage (buggy cases diagnosed) | 3/4 (75%) |
| Selective accuracy (diagnoses matching truth) | 3/3 (100%) |
| False-positive diagnoses | 0 |
| False negatives (modelled bugs not diagnosed) | 0/3 (0%) |
| Correct code with no failure observed | 1/1 (100%) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 1 |
| Reproducible across 2 runs | 5/5 (100%) |

Error-model pairs the suite cannot separate: none.

| Case | Truth | Outcome | Selected model | Result | Reproducible |
| --- | --- | --- | --- | --- | --- |
| bounded_by_last_index.cpp | hi_init_last_index | hypothesis_supported | hi_init_last_index | true_diagnosis | yes |
| closed_interval_correct.cpp | correct | no_failure_observed | — | correct_pass | yes |
| inclusive_end_formula.cpp | inclusive_count | hypothesis_supported | inclusive_count | true_diagnosis | yes |
| presence_only.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| same_comparison_twice.cpp | upper_uses_strict | hypothesis_supported | upper_uses_strict | true_diagnosis | yes |

## last-less-than (content 3d52811ae14b)

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 5 (4 / 1) |
| Coverage (buggy cases diagnosed) | 3/4 (75%) |
| Selective accuracy (diagnoses matching truth) | 3/3 (100%) |
| False-positive diagnoses | 0 |
| False negatives (modelled bugs not diagnosed) | 0/3 (0%) |
| Correct code with no failure observed | 1/1 (100%) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 1 |
| Reproducible across 2 runs | 5/5 (100%) |

Error-model pairs the suite cannot separate: none.

| Case | Truth | Outcome | Selected model | Result | Reproducible |
| --- | --- | --- | --- | --- | --- |
| closed_interval_correct.cpp | correct | no_failure_observed | — | correct_pass | yes |
| closed_interval_le.cpp | uses_le | hypothesis_supported | uses_le | true_diagnosis | yes |
| le_and_clamped.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| never_negative.cpp | clamps_to_zero | hypothesis_supported | clamps_to_zero | true_diagnosis | yes |
| returns_count_below.cpp | returns_insertion_point | hypothesis_supported | returns_insertion_point | true_diagnosis | yes |

## lower-bound (content 41dd7907bd39)

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 7 (5 / 2) |
| Coverage (buggy cases diagnosed) | 3/5 (60%) |
| Selective accuracy (diagnoses matching truth) | 3/3 (100%) |
| False-positive diagnoses | 0 |
| False negatives (modelled bugs not diagnosed) | 0/3 (0%) |
| Correct code with no failure observed | 2/2 (100%) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 2 |
| Reproducible across 2 runs | 7/7 (100%) |

Error-model pairs the suite cannot separate: none.

| Case | Truth | Outcome | Selected model | Result | Reproducible |
| --- | --- | --- | --- | --- | --- |
| classic_exact_search.cpp | exact_match_sentinel | hypothesis_supported | exact_match_sentinel | true_diagnosis | yes |
| closed_interval_correct.cpp | correct | no_failure_observed | — | correct_pass | yes |
| correct_iterative.cpp | correct | no_failure_observed | — | correct_pass | yes |
| double_bug.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| empty_returns_minus_one.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| recursive_last_index.cpp | hi_init_last_index | hypothesis_supported | hi_init_last_index | true_diagnosis | yes |
| upper_bound_closed.cpp | upper_bound_confusion | hypothesis_supported | upper_bound_confusion | true_diagnosis | yes |

## Limitations

* Synthetic held-out cases were written by the same author as the error models, so they share that author's idea of each bug.
* The held-out set is small and is not drawn from real student submissions; its distribution says nothing about how often each bug occurs in practice.
* Selective accuracy here is an upper bound on what real students' code will show.
* These results are about the diagnostic method, not about learning; they are not evidence that CodeAdapt helps anyone learn.
* No test checks the O(log n) requirement: a linear scan passes every suite, so nothing here says anything about complexity.
