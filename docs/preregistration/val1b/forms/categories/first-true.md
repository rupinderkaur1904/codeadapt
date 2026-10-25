# Categories for problem: First true

Choose the one category that best matches **your own stage-1 description** of the
primary error. If none fits, use `other-single` (and describe it), `multiple`, or
`unclear`. Do not change your stage-1 answers.

| Id | Description |
| --- | --- |
| C1 | Loops while hi - lo > 1 and returns lo unchecked, so the answer is wrong when it is lo + 1. |
| C2 | Returns the index of the last 0 (one less than the first 1). |
| C3 | Initialises hi = n - 1 with a half-open loop, so the answer n (no 1 present) is unreachable. |
| C4 | Sets lo = mid instead of lo = mid + 1, so the range stops shrinking when two candidates remain. |
| C5 | Uses a closed range with lo <= hi but updates hi = mid, so the loop never ends once lo == hi on a 1. |
| C6 | Returns -1 instead of flags.size() when there is no 1. |
| C7 | Initialises lo = 1, so index 0 is never a candidate answer. |
| C8 | Returns as soon as flags[mid] is 1, which is some 1 but not necessarily the first. |
| C9 | In a half-open loop, a 1 at mid sets hi = mid - 1, discarding flags[mid], which may itself be the first 1. |
| other-single | One error that is not in this list |
| multiple | Two or more independent errors |
| unclear | You cannot tell |

## Skills

| Id | Skill |
| --- | --- |
| S1 | Initialising and updating the bounds of the search space so every candidate answer stays reachable. |
| S2 | Ensuring each iteration shrinks the search space so the loop terminates. |
| S4 | Returning what the specification asks for, including when the target is absent. |
| none | None of these |
| uncertain | You cannot tell |
