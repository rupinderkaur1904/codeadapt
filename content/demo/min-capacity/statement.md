Implement

```cpp
int min_capacity(const std::vector<int>& weights, int days);
```

Packages with the given `weights` must be shipped **in the given order** within `days` days.
Each day, packages are loaded one after another, starting where the previous day stopped, and
the total weight loaded on one day may not exceed the ship's capacity. Return the smallest
capacity that ships every package within `days` days.

Constraints: `1 <= weights.size() <= 100000`, `1 <= weights[i] <= 10000`,
`1 <= days <= weights.size()`. The answer always fits in an `int`.

Your solution must run in O(n log W) time, where W is the total weight. Do not call
`std::lower_bound`, `std::upper_bound`, `std::equal_range` or `std::partition_point`.

Examples: `weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], days = 5 → 15`;
`weights = [3, 2, 2, 4, 1, 4], days = 3 → 6`.
