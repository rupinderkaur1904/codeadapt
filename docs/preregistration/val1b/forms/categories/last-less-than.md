# Categories for problem: Last element less than

Choose the one category that best matches **your own stage-1 description** of the
primary error. If none fits, use `other-single` (and describe it), `multiple`, or
`unclear`. Do not change your stage-1 answers.

| Id | Description |
| --- | --- |
| C1 | Returns 0 instead of -1 when no element is less than the target. |
| C2 | Returns the boundary (the first index with a[i] >= target) instead of the index just before it. |
| C3 | Initialises hi = n - 1 with a half-open loop, so the boundary n is unreachable and the last index is never returned. |
| C4 | Updates lo = mid instead of lo = mid + 1; when two candidates remain the search space stops shrinking and the loop does not terminate. |
| C5 | Uses a[mid] <= target where a[mid] < target is required, so it returns the last element less than or equal to the target. |
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
