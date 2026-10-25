Implement

```cpp
int pivot_index(const std::vector<int>& a);
```

Return the **first** index `i` such that the sum of the elements strictly to the left of `i`
equals the sum of the elements strictly to its right. An empty side sums to 0. Return `-1` if no
such index exists.

Constraints: `1 <= a.size() <= 100000`, `-10^4 <= a[i] <= 10^4`.

Your solution must run in O(n) time.

Examples: `a = [1, 7, 3, 6, 5, 6] → 3`; `a = [1, 2, 3] → -1`; `a = [2, 1, -1] → 0`.
