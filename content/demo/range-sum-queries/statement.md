Implement

```cpp
std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries);
```

For each query `(l, r)`, return the sum `a[l] + a[l + 1] + ... + a[r]` (0-based, both ends
included), in query order.

Constraints: `1 <= a.size(), queries.size() <= 100000`, `-10^4 <= a[i] <= 10^4`,
`0 <= l <= r < a.size()`.

Your solution must run in O(n + q) time.

Examples: `a = [3, -1, 4, 1, 5, -9]`, queries `(0, 2), (1, 4), (2, 5)` → `[6, 9, 1]`.
