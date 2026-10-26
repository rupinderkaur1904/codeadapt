# Method comparison (heldout cases)

All methods diagnosed the same collected evidence for each case. Raw counts; the cases are synthetic and written by the error models' author, so this is not an accuracy estimate for real students.

| | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` | `fingerprint_consistency v1.3` |
| --- | --- | --- | --- |
| Cases | 6 | 6 | 6 |
| Buggy cases | 5 | 5 | 5 |
| Coverage (diagnosed buggy cases) | 4/5 | 3/5 | 2/5 |
| Correct diagnoses | 4 | 3 | 2 |
| Incorrect diagnoses (buggy case, wrong model) | 0 | 0 | 0 |
| False alarms on correct programs | 0 | 0 | 0 |
| False-positive diagnoses (model is not the truth) | 0 | 0 | 0 |
| Abstentions on buggy cases | 1 | 2 | 3 |
| Abstentions by outcome | unmodelled_behaviour 1 | non_termination_observed 1, unmodelled_behaviour 1 | insufficient_evidence 1, non_termination_observed 1, unmodelled_behaviour 1 |

## Cases involving `hi_init_last_index` (as truth or as diagnosis)

| Problem | Case | Truth | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` | `fingerprint_consistency v1.3` |
| --- | --- | --- | --- | --- | --- |
| count-occurrences | bounded_by_last_index.cpp | hi_init_last_index | hypothesis_supported (hi_init_last_index) → true_diagnosis | hypothesis_supported (hi_init_last_index) → true_diagnosis | hypothesis_supported (hi_init_last_index) → true_diagnosis |

## Cases involving `stops_at_first_match` (as truth or as diagnosis)

None.

## Cases whose outcome differs between methods

| Problem | Case | Truth | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` | `fingerprint_consistency v1.3` |
| --- | --- | --- | --- | --- | --- |
| count-occurrences | same_comparison_twice.cpp | upper_uses_strict | hypothesis_supported (upper_uses_strict) → true_diagnosis | hypothesis_supported (upper_uses_strict) → true_diagnosis | insufficient_evidence → abstained |
| count-occurrences | two_searches_stalled_left.cpp | no_progress_update | hypothesis_supported (no_progress_update) → true_diagnosis | non_termination_observed → symptom_reported | non_termination_observed → symptom_reported |
