# CodeAdapt synthetic evaluation report

Method `fingerprint_consistency` v1.1; case set `calibration`; data class `synthetic`; each case run 2 times; g++ (GCC) 14.2.0 on `runc`.

## Overall

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 5 (5 / 0) |
| Coverage (buggy cases diagnosed) | 2/5 (40%) |
| Selective accuracy (diagnoses matching truth) | 1/2 (50%) |
| False-positive diagnoses | 1 |
| False negatives (modelled bugs not diagnosed) | 0/1 (0%) |
| Correct code with no failure observed | 0/0 (n/a) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 3 |
| Reproducible across 2 runs | 5/5 (100%) |

## lower-bound (content 871602bc2bba)

| Metric | Value |
| --- | --- |
| Cases (buggy / correct) | 5 (5 / 0) |
| Coverage (buggy cases diagnosed) | 2/5 (40%) |
| Selective accuracy (diagnoses matching truth) | 1/2 (50%) |
| False-positive diagnoses | 1 |
| False negatives (modelled bugs not diagnosed) | 0/1 (0%) |
| Correct code with no failure observed | 0/0 (n/a) |
| Abstentions on buggy cases, by outcome | unmodelled_behaviour: 3 |
| Reproducible across 2 runs | 5/5 (100%) |

Error-model pairs the suite cannot separate: none.

| Case | Truth | Outcome | Selected model | Result | Reproducible |
| --- | --- | --- | --- | --- | --- |
| clamp_to_last_index.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| clamp_with_empty_guard.cpp | unmodelled | hypothesis_supported | hi_init_last_index | false_diagnosis | yes |
| exact_search_walk_back.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| last_of_run.cpp | unmodelled | unmodelled_behaviour | — | abstained | yes |
| stop_on_match_upper_mid.cpp | stops_at_first_match | hypothesis_supported | stops_at_first_match | true_diagnosis | yes |

## Limitations

* Synthetic held-out cases were written by the same author as the error models, so they share that author's idea of each bug.
* The held-out set is small and is not drawn from real student submissions; its distribution says nothing about how often each bug occurs in practice.
* Selective accuracy here is an upper bound on what real students' code will show.
* These results are about the diagnostic method, not about learning; they are not evidence that CodeAdapt helps anyone learn.
* No test checks the O(log n) requirement: a linear scan passes every suite, so nothing here says anything about complexity.
