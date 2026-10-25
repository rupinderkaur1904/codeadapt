# Method comparison (calibration cases)

All methods diagnosed the same collected evidence for each case. Raw counts; the cases are synthetic and written by the error models' author, so this is not an accuracy estimate for real students.

| | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` |
| --- | --- | --- |
| Cases | 5 | 5 |
| Buggy cases | 5 | 5 |
| Coverage (diagnosed buggy cases) | 2/5 | 2/5 |
| Correct diagnoses | 1 | 1 |
| Incorrect diagnoses (buggy case, wrong model) | 1 | 1 |
| False alarms on correct programs | 0 | 0 |
| False-positive diagnoses (model is not the truth) | 1 | 1 |
| Abstentions on buggy cases | 3 | 3 |
| Abstentions by outcome | unmodelled_behaviour 3 | unmodelled_behaviour 3 |

## Cases involving `hi_init_last_index` (as truth or as diagnosis)

| Problem | Case | Truth | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` |
| --- | --- | --- | --- | --- |
| lower-bound | clamp_with_empty_guard.cpp | unmodelled | hypothesis_supported (hi_init_last_index) → false_diagnosis | hypothesis_supported (hi_init_last_index) → false_diagnosis |

## Cases involving `stops_at_first_match` (as truth or as diagnosis)

| Problem | Case | Truth | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` |
| --- | --- | --- | --- | --- |
| lower-bound | stop_on_match_upper_mid.cpp | stops_at_first_match | hypothesis_supported (stops_at_first_match) → true_diagnosis | hypothesis_supported (stops_at_first_match) → true_diagnosis |

## Cases whose outcome differs between methods

None.
