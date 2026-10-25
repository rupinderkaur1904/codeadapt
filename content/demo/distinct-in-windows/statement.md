Implement

```cpp
std::vector<int> distinct_in_windows(const std::vector<int>& a, int k);
```

For every window of `k` consecutive elements, from left to right, return the number of
**distinct values** in that window. The result has `a.size() - k + 1` entries.

Constraints: `1 <= k <= a.size() <= 100000`, `0 <= a[i] <= 10^9`.

Your solution must run in O(n) expected time (or O(n log n)).

Examples: `a = [1, 2, 1, 3, 4, 2, 3], k = 4 → [3, 4, 4, 3]`; `a = [7, 7, 7, 7, 7], k = 2 →
[1, 1, 1, 1]`.
