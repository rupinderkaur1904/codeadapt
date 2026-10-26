# Method comparison (heldout cases)

All methods diagnosed the same collected evidence for each case. Raw counts; the cases are synthetic and written by the error models' author, so this is not an accuracy estimate for real students.

| | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` | `fingerprint_consistency v1.3` |
| --- | --- | --- | --- |
| Cases | 12 | 12 | 12 |
| Buggy cases | 10 | 10 | 10 |
| Coverage (diagnosed buggy cases) | 8/10 | 6/10 | 6/10 |
| Correct diagnoses | 8 | 6 | 6 |
| Incorrect diagnoses (buggy case, wrong model) | 0 | 0 | 0 |
| False alarms on correct programs | 0 | 0 | 0 |
| False-positive diagnoses (model is not the truth) | 0 | 0 | 0 |
| Abstentions on buggy cases | 2 | 4 | 4 |
| Abstentions by outcome | unmodelled_behaviour 2 | non_termination_observed 2, unmodelled_behaviour 2 | non_termination_observed 2, unmodelled_behaviour 2 |

## Cases involving `hi_init_last_index` (as truth or as diagnosis)

| Problem | Case | Truth | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` | `fingerprint_consistency v1.3` |
| --- | --- | --- | --- | --- | --- |
| lower-bound | recursive_last_index.cpp | hi_init_last_index | hypothesis_supported (hi_init_last_index) → true_diagnosis | hypothesis_supported (hi_init_last_index) → true_diagnosis | hypothesis_supported (hi_init_last_index) → true_diagnosis |

## Cases involving `stops_at_first_match` (as truth or as diagnosis)

| Problem | Case | Truth | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` | `fingerprint_consistency v1.3` |
| --- | --- | --- | --- | --- | --- |
| lower-bound | recursive_early_equal.cpp | stops_at_first_match | hypothesis_supported (stops_at_first_match) → true_diagnosis | hypothesis_supported (stops_at_first_match) → true_diagnosis | hypothesis_supported (stops_at_first_match) → true_diagnosis |

## Cases whose outcome differs between methods

| Problem | Case | Truth | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` | `fingerprint_consistency v1.3` |
| --- | --- | --- | --- | --- | --- |
| lower-bound | negated_closed_loop.cpp | closed_loop_hi_mid | hypothesis_supported (closed_loop_hi_mid) → true_diagnosis | non_termination_observed → symptom_reported | non_termination_observed → symptom_reported |
| lower-bound | size_t_stuck_left.cpp | no_progress_update | hypothesis_supported (no_progress_update) → true_diagnosis | non_termination_observed → symptom_reported | non_termination_observed → symptom_reported |
