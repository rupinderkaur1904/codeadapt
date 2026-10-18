# CodeAdapt synthetic evaluation report

Method `fingerprint_consistency` v1.1; case set `heldout`; data class `synthetic`; each case run 2 times; g++ (GCC) 14.2.0 on `runc`.

## Overall

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 32 (26 / 6) |
| Coverage (buggy cases diagnosed) | 19/26 (73%) |
| Selective accuracy (diagnoses matching truth) | 19/19 (100%) |
| False-positive diagnoses | 0 |
| False negatives (modelled bugs not diagnosed) | 1/20 (5%) |
| Correct code with no failure observed | 6/6 (100%) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 7 |
| Reproducible across 2 runs | 32/32 (100%) |

## count-occurrences (content d1b043c04574)

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 6 (5 / 1) |
| Coverage (buggy cases diagnosed) | 4/5 (80%) |
| Selective accuracy (diagnoses matching truth) | 4/4 (100%) |
| False-positive diagnoses | 0 |
| False negatives (modelled bugs not diagnosed) | 0/4 (0%) |
| Correct code with no failure observed | 1/1 (100%) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 1 |
| Reproducible across 2 runs | 6/6 (100%) |

Error-model pairs the suite cannot separate: none.

| Case | Truth | Outcome | Selected model | Result | Reproducible |
| --- | --- | --- | --- | --- | --- |
| bounded_by_last_index.cpp | hi_init_last_index | hypothesis_supported | hi_init_last_index | true_diagnosis | yes |
| closed_interval_correct.cpp | correct | no_failure_observed | — | correct_pass | yes |
| inclusive_end_formula.cpp | inclusive_count | hypothesis_supported | inclusive_count | true_diagnosis | yes |
| presence_only.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| same_comparison_twice.cpp | upper_uses_strict | hypothesis_supported | upper_uses_strict | true_diagnosis | yes |
| two_searches_stalled_left.cpp | no_progress_update | hypothesis_supported | no_progress_update | true_diagnosis | yes |

## first-true (content b69c5efa3b39)

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 7 (5 / 2) |
| Coverage (buggy cases diagnosed) | 2/5 (40%) |
| Selective accuracy (diagnoses matching truth) | 2/2 (100%) |
| False-positive diagnoses | 0 |
| False negatives (modelled bugs not diagnosed) | 1/3 (33%) |
| Correct code with no failure observed | 2/2 (100%) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 3 |
| Reproducible across 2 runs | 7/7 (100%) |

Error-model pairs the suite cannot separate: none.

| Case | Truth | Outcome | Selected model | Result | Reproducible |
| --- | --- | --- | --- | --- | --- |
| classic_found_return.cpp | returns_any_true | unmodelled_behaviour | — | abstained | yes |
| closed_interval_answer_var.cpp | correct | no_failure_observed | — | correct_pass | yes |
| empty_minus_one.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| power_of_two_steps.cpp | correct | no_failure_observed | — | correct_pass | yes |
| recursive_from_one.cpp | lo_init_one | hypothesis_supported | lo_init_one | true_diagnosis | yes |
| right_drops_mid.cpp | hi_skips_candidate | hypothesis_supported | hi_skips_candidate | true_diagnosis | yes |
| skips_and_sentinel.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |

## last-less-than (content 3d52811ae14b)

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 7 (6 / 1) |
| Coverage (buggy cases diagnosed) | 5/6 (83%) |
| Selective accuracy (diagnoses matching truth) | 5/5 (100%) |
| False-positive diagnoses | 0 |
| False negatives (modelled bugs not diagnosed) | 0/5 (0%) |
| Correct code with no failure observed | 1/1 (100%) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 1 |
| Reproducible across 2 runs | 7/7 (100%) |

Error-model pairs the suite cannot separate: none.

| Case | Truth | Outcome | Selected model | Result | Reproducible |
| --- | --- | --- | --- | --- | --- |
| closed_from_last_index.cpp | hi_init_last_index | hypothesis_supported | hi_init_last_index | true_diagnosis | yes |
| closed_interval_correct.cpp | correct | no_failure_observed | — | correct_pass | yes |
| closed_interval_le.cpp | uses_le | hypothesis_supported | uses_le | true_diagnosis | yes |
| le_and_clamped.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| never_negative.cpp | clamps_to_zero | hypothesis_supported | clamps_to_zero | true_diagnosis | yes |
| returns_count_below.cpp | returns_insertion_point | hypothesis_supported | returns_insertion_point | true_diagnosis | yes |
| while_true_stalls.cpp | no_progress_update | hypothesis_supported | no_progress_update | true_diagnosis | yes |

## lower-bound (content 871602bc2bba)

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 12 (10 / 2) |
| Coverage (buggy cases diagnosed) | 8/10 (80%) |
| Selective accuracy (diagnoses matching truth) | 8/8 (100%) |
| False-positive diagnoses | 0 |
| False negatives (modelled bugs not diagnosed) | 0/8 (0%) |
| Correct code with no failure observed | 2/2 (100%) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 2 |
| Reproducible across 2 runs | 12/12 (100%) |

Error-model pairs the suite cannot separate: none.

| Case | Truth | Outcome | Selected model | Result | Reproducible |
| --- | --- | --- | --- | --- | --- |
| answer_var_returns_right.cpp | returns_wrong_pointer | hypothesis_supported | returns_wrong_pointer | true_diagnosis | yes |
| classic_exact_search.cpp | exact_match_sentinel | hypothesis_supported | exact_match_sentinel | true_diagnosis | yes |
| closed_interval_correct.cpp | correct | no_failure_observed | — | correct_pass | yes |
| correct_iterative.cpp | correct | no_failure_observed | — | correct_pass | yes |
| double_bug.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| empty_returns_minus_one.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| negated_closed_loop.cpp | closed_loop_hi_mid | hypothesis_supported | closed_loop_hi_mid | true_diagnosis | yes |
| recursive_early_equal.cpp | stops_at_first_match | hypothesis_supported | stops_at_first_match | true_diagnosis | yes |
| recursive_last_index.cpp | hi_init_last_index | hypothesis_supported | hi_init_last_index | true_diagnosis | yes |
| reversed_test_drops_mid.cpp | hi_skips_candidate | hypothesis_supported | hi_skips_candidate | true_diagnosis | yes |
| size_t_stuck_left.cpp | no_progress_update | hypothesis_supported | no_progress_update | true_diagnosis | yes |
| upper_bound_closed.cpp | upper_bound_confusion | hypothesis_supported | upper_bound_confusion | true_diagnosis | yes |

## Limitations

* Synthetic held-out cases were written by the same author as the error models, so they share that author's idea of each bug.
* The held-out set is small and is not drawn from real student submissions; its distribution says nothing about how often each bug occurs in practice.
* Selective accuracy here is an upper bound on what real students' code will show.
* These results are about the diagnostic method, not about learning; they are not evidence that CodeAdapt helps anyone learn.
* No test checks the O(log n) requirement: a linear scan passes every suite, so nothing here says anything about complexity.
