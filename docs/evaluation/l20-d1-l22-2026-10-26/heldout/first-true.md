# Method comparison (heldout cases)

All methods diagnosed the same collected evidence for each case. Raw counts; the cases are synthetic and written by the error models' author, so this is not an accuracy estimate for real students.

| | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` | `fingerprint_consistency v1.3` |
| --- | --- | --- | --- |
| Cases | 7 | 7 | 7 |
| Buggy cases | 5 | 5 | 5 |
| Coverage (diagnosed buggy cases) | 2/5 | 2/5 | 2/5 |
| Correct diagnoses | 2 | 2 | 2 |
| Incorrect diagnoses (buggy case, wrong model) | 0 | 0 | 0 |
| False alarms on correct programs | 0 | 0 | 0 |
| False-positive diagnoses (model is not the truth) | 0 | 0 | 0 |
| Abstentions on buggy cases | 3 | 3 | 3 |
| Abstentions by outcome | unmodelled_behaviour 3 | unmodelled_behaviour 3 | unmodelled_behaviour 3 |

## Cases involving `hi_init_last_index` (as truth or as diagnosis)

None.

## Cases involving `stops_at_first_match` (as truth or as diagnosis)

None.

## Cases whose outcome differs between methods

None.
