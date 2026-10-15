# Lower bound

Implement

```cpp
int lower_bound_index(const std::vector<int>& a, int target);
```

`a` is sorted in non-decreasing order and may be empty or contain repeated values.
Return the smallest index `i` such that `a[i] >= target`. If no such index exists, return
`a.size()`.

Your solution must run in O(log n) time. Do not call `std::lower_bound`,
`std::upper_bound`, `std::equal_range` or `std::partition_point`.

Examples: `a = [1, 3, 5, 7]`: `target = 5 → 2`; `target = 4 → 2`; `target = 8 → 4`.
