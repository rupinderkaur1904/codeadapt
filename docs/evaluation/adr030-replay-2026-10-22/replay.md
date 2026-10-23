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

## Checks

- Recorded runs reproduced exactly: v1.1 1366, v1.2 1066 (VAL1-A records v1.1 only).
- Runs on which production method 1.3 (ADR-030, once implemented) equals the candidate: 1366.
- Programs whose v1.1 result differs between their 2 runs: 1
    - val1a2/first-true/C_AOR_018 (unreliable): unreliable_evidence / unmodelled_behaviour
- Programs whose v1.2 result differs between their 2 runs: 1
    - val1a2/first-true/C_AOR_018 (unreliable): unreliable_evidence / non_termination_observed
- Programs whose candidate result differs between their 2 runs: 1
    - val1a2/first-true/C_AOR_018 (unreliable): unreliable_evidence / non_termination_observed

A program whose runs differ is execution non-reproducibility in the recorded evidence, not
a property of a method: VAL1-A/A2 classify it `unreliable` and leave it out of every scored
count above. The candidate agrees with v1.2 on every run of every such program.
- Candidate identical to v1.2 on every run of every unchanged program: True
