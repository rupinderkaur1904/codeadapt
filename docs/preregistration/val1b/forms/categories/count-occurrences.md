# Categories for problem: Count occurrences

Choose the one category that best matches **your own stage-1 description** of the
primary error. If none fits, use `other-single` (and describe it), `multiple`, or
`unclear`. Do not change your stage-1 answers.

| Id | Description |
| --- | --- |
| C1 | Initialises hi = n - 1 with a half-open loop, so a boundary can never reach n and runs of the target at the end of the array are undercounted. |
| C2 | Returns upper - lower + 1, treating two half-open boundaries as if they were inclusive indices. |
| C3 | Updates lo = mid instead of lo = mid + 1; when two candidates remain the search space stops shrinking and the loop does not terminate. |
| C4 | Both boundaries use a[mid] < target, so the upper boundary equals the lower one and the count is always 0. |
| other-single | One error that is not in this list |
| multiple | Two or more independent errors |
| unclear | You cannot tell |

## Skills

| Id | Skill |
| --- | --- |
| S1 | Initialising and updating the bounds of the search space so every candidate answer stays reachable. |
| S2 | Ensuring each iteration shrinks the search space so the loop terminates. |
| S3 | Choosing the comparison so equal elements land on the correct side of the boundary. |
| S4 | Returning what the specification asks for, including when the target is absent. |
| none | None of these |
| uncertain | You cannot tell |
