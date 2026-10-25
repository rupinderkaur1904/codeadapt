# Method comparison (heldout cases)

All methods diagnosed the same collected evidence for each case. Raw counts; the cases are synthetic and written by the error models' author, so this is not an accuracy estimate for real students.

| | `fingerprint_consistency v1.1` | `fingerprint_consistency v1.2` | `fingerprint_consistency v1.3` |
| --- | --- | --- | --- |
| Cases | 8 | 8 | 8 |
| Buggy cases | 6 | 6 | 6 |
| Coverage (diagnosed buggy cases) | 5/6 | 5/6 | 5/6 |
| Correct diagnoses | 4 | 4 | 4 |
| Incorrect diagnoses (buggy case, wrong model) | 1 | 1 | 1 |
| False alarms on correct programs | 0 | 0 | 0 |
| False-positive diagnoses (model is not the truth) | 1 | 1 | 1 |
| Abstentions on buggy cases | 1 | 1 | 1 |
| Abstentions by outcome | unmodelled_behaviour 1 | unmodelled_behaviour 1 | unmodelled_behaviour 1 |

## Cases involving `hi_init_last_index` (as truth or as diagnosis)

None.

## Cases involving `stops_at_first_match` (as truth or as diagnosis)

None.

## Cases whose outcome differs between methods

None.
