# ADR-030 replay: v1.1, v1.2 and the candidate rule, case by case

Recorded evidence only; nothing re-executed. Every recorded v1.2 (and v1.1) outcome and
model was reproduced before these numbers were computed. Synthetic and author-written
cases only: not real-student evidence.

## Summary

| Set | Scored programs | Method | Named | Named correctly | Wrong names | `incorrect` skill observations on a wrong skill |
| --- | --- | --- | --- | --- | --- | --- |
| heldout | 26 | v1.1 | 19 | 19 | 0 | 0 |
| heldout | 26 | v1.2 | 15 | 15 | 0 | 0 |
| heldout | 26 | candidate | 14 | 14 | 0 | 0 |
| calibration | 5 | v1.1 | 2 | 1 | 1 | 0 |
| calibration | 5 | v1.2 | 2 | 1 | 1 | 0 |
| calibration | 5 | candidate | 2 | 1 | 1 | 0 |
| val1a | 98 | v1.1 | 32 | 27 | 5 | 5 |
| val1a | 98 | v1.2 | 10 | 10 | 0 | 0 |
| val1a | 98 | candidate | 10 | 10 | 0 | 0 |
| val1a2 | 323 | v1.1 | 94 | 75 | 19 | 19 |
| val1a2 | 323 | v1.2 | 50 | 39 | 11 | 11 |
| val1a2 | 323 | candidate | 30 | 30 | 0 | 0 |

Scored programs: incorrect programs only (held-out and calibration: every case whose truth is
not `correct`; VAL1-A/A2: `incorrect_failing`). Correctness: held-out/calibration against the
author's truth label; VAL1-A/A2 against the behavioural label (PLAN.md §4 of VAL1-A2).

## Every case the candidate changes (v1.2 → candidate)

| Set | Case | Truth / label | v1.2 name | Was it right? | Rule | Feedback after | Skill observations after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| heldout | count-occurrences/same_comparison_twice.cpp | upper_uses_strict | upper_uses_strict | yes | 8a | failing_cases | problem_specification:correct |
| val1a2 | count-occurrences/A_NEG_014 | none | upper_uses_strict | no | 8a | failing_cases | none |
| val1a2 | count-occurrences/A_ROR_008 | model:upper_uses_strict | upper_uses_strict | yes | 8a | failing_cases | problem_specification:correct |
| val1a2 | count-occurrences/A_ROR_009 | none | upper_uses_strict | no | 8a | failing_cases | none |
| val1a2 | count-occurrences/A_ROR_010 | none | upper_uses_strict | no | 8a | failing_cases | none |
| val1a2 | count-occurrences/A_ROR_027 | model:upper_uses_strict | upper_uses_strict | yes | 8a | failing_cases | problem_specification:correct |
| val1a2 | count-occurrences/A_ROR_034 | model:upper_uses_strict | upper_uses_strict | yes | 8a | failing_cases | problem_specification:correct |
| val1a2 | count-occurrences/A_SDL_046 | model:no_progress_update | upper_uses_strict | no | 8a | failing_cases | problem_specification:correct |
| val1a2 | count-occurrences/B_NEG_020 | none | upper_uses_strict | no | 8a | failing_cases | none |
| val1a2 | count-occurrences/B_ROR_014 | none | upper_uses_strict | no | 8a | failing_cases | none |
| val1a2 | count-occurrences/B_ROR_015 | none | upper_uses_strict | no | 8a,8b | failing_cases | none |
| val1a2 | count-occurrences/B_ROR_035 | model:upper_uses_strict | upper_uses_strict | yes | 8a | failing_cases | problem_specification:correct |
| val1a2 | count-occurrences/B_ROR_042 | model:upper_uses_strict | upper_uses_strict | yes | 8a | failing_cases | problem_specification:correct |
| val1a2 | count-occurrences/B_SDL_048 | model:upper_uses_strict | upper_uses_strict | yes | 8a | failing_cases | problem_specification:correct |
| val1a2 | count-occurrences/C_NEG_010 | none | upper_uses_strict | no | 8a | failing_cases | none |
| val1a2 | count-occurrences/C_ROR_003 | none | upper_uses_strict | no | 8a | failing_cases | none |
| val1a2 | count-occurrences/C_ROR_004 | model:upper_uses_strict | upper_uses_strict | yes | 8a | failing_cases | problem_specification:correct |
| val1a2 | count-occurrences/C_ROR_007 | none | upper_uses_strict | no | 8a | failing_cases | none |
| val1a2 | count-occurrences/C_ROR_025 | model:upper_uses_strict | upper_uses_strict | yes | 8a | failing_cases | problem_specification:correct |
| val1a2 | count-occurrences/C_ROR_032 | model:upper_uses_strict | upper_uses_strict | yes | 8a | failing_cases | problem_specification:correct |
| val1a2 | first-true/B_UOI_031 | none | stops_one_early | no | 8b | failing_cases | none |

Cases whose diagnosis is unchanged but whose consequences differ: 0.

Changed cases by set and rule: heldout 8a: 1, val1a2 8a: 18, val1a2 8a+8b: 1, val1a2 8b: 1

Programs whose candidate result differs between runs: 1 ['val1a2/first-true/C_AOR_018']
