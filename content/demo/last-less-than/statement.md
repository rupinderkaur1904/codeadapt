Implement

```cpp
int last_less_than(const std::vector<int>& a, int target);
```

`a` is sorted in non-decreasing order and may be empty or contain repeated values.
Return the largest index `i` such that `a[i] < target`. If no such index exists, return
`-1`.

Your solution must run in O(log n) time. Do not call `std::lower_bound`,
`std::upper_bound`, `std::equal_range` or `std::partition_point`.

Examples: `a = [1, 3, 3, 7]`: `target = 3 → 0`; `target = 5 → 2`; `target = 1 → -1`.
