# Categories for problem: Lower bound

Choose the one category that best matches **your own stage-1 description** of the
primary error. If none fits, use `other-single` (and describe it), `multiple`, or
`unclear`. Do not change your stage-1 answers.

| Id | Description |
| --- | --- |
| C1 | Uses a[mid] <= target where a[mid] < target is required, so the search returns the first element strictly greater than the target (upper bound). |
| C2 | Correct closed-interval search that returns hi instead of lo; on exit hi == lo - 1, the last index whose element is below the target. |
| C3 | Initialises hi = n - 1 with a half-open loop, so the answer n (no element >= target) is unreachable. |
| C4 | Updates lo = mid instead of lo = mid + 1; when two candidates remain the search space stops shrinking and the loop does not terminate. |
| C5 | Closed-interval loop (lo <= hi, hi = n - 1) with the half-open update hi = mid; once lo == hi and a[mid] >= target the range stops shrinking and the loop does not terminate. |
| C6 | Returns as soon as a[mid] == target, which is not necessarily the first occurrence when values repeat. |
| C7 | Half-open loop that sets hi = mid - 1 when a[mid] >= target, discarding a[mid], which may itself be the answer. |
| C8 | Implements exact-match search: returns some index holding the target, or -1 when the target is absent. |
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
