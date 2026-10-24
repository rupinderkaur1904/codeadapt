Implement

```cpp
int upper_bound_index(const std::vector<int>& a, int target);
```

`a` is sorted in non-decreasing order and may be empty or contain repeated values.
Return the smallest index `i` such that `a[i] > target` (strictly greater). If no such index
exists, return `a.size()`.

Your solution must run in O(log n) time. Do not call `std::lower_bound`,
`std::upper_bound`, `std::equal_range` or `std::partition_point`.

Examples: `a = [1, 3, 3, 5]`: `target = 3 → 3`; `target = 4 → 3`; `target = 5 → 4`;
`target = 0 → 0`.
