Implement

```cpp
int last_occurrence(const std::vector<int>& a, int target);
```

`a` is sorted in non-decreasing order and may be empty or contain repeated values.
Return the largest index `i` such that `a[i] == target`. If the target does not occur in
`a`, return `-1`.

Your solution must run in O(log n) time. Do not call `std::lower_bound`,
`std::upper_bound`, `std::equal_range`, `std::partition_point` or `std::find`.

Examples: `a = [1, 3, 3, 3, 5]`: `target = 3 → 3`; `target = 4 → -1`; `target = 5 → 4`.
