# Method comparison (heldout cases)

All methods diagnosed the same collected evidence for each case. Raw counts; the cases are synthetic and written by the error models' author, so this is not an accuracy estimate for real students.

| | `fingerprint_consistency v1.1` | `fingerprint_consistency v2-candidate` |
| --- | --- | --- |
| Cases | 17 | 17 |
| Buggy cases | 13 | 13 |
| Coverage (diagnosed buggy cases) | 9/13 | 7/13 |
| Correct diagnoses | 9 | 7 |
| Incorrect diagnoses (buggy case, wrong model) | 0 | 0 |
| False alarms on correct programs | 0 | 0 |
| False-positive diagnoses (model is not the truth) | 0 | 0 |
| Abstentions on buggy cases | 4 | 6 |
| Abstentions by outcome | unmodelled_behaviour 4 | insufficient_evidence 2, unmodelled_behaviour 4 |

## Cases involving `hi_init_last_index` (as truth or as diagnosis)

| Problem | Case | Truth | `fingerprint_consistency v1.1` | `fingerprint_consistency v2-candidate` |
| --- | --- | --- | --- | --- |
| count-occurrences | bounded_by_last_index.cpp | hi_init_last_index | hypothesis_supported (hi_init_last_index) → true_diagnosis | insufficient_evidence → abstained |
| lower-bound | recursive_last_index.cpp | hi_init_last_index | hypothesis_supported (hi_init_last_index) → true_diagnosis | insufficient_evidence → abstained |

## Cases involving `stops_at_first_match` (as truth or as diagnosis)

None.

## Cases whose outcome differs between methods

| Problem | Case | Truth | `fingerprint_consistency v1.1` | `fingerprint_consistency v2-candidate` |
| --- | --- | --- | --- | --- |
| count-occurrences | bounded_by_last_index.cpp | hi_init_last_index | hypothesis_supported (hi_init_last_index) → true_diagnosis | insufficient_evidence → abstained |
| lower-bound | recursive_last_index.cpp | hi_init_last_index | hypothesis_supported (hi_init_last_index) → true_diagnosis | insufficient_evidence → abstained |
