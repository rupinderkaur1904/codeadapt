Implement

```cpp
int search_index(const std::vector<int>& a, int target);
```

`a` is sorted in strictly increasing order (no repeated values) and may be empty. Return the
index `i` with `a[i] == target`, or `-1` if the target is not in `a`.

Your solution must run in O(log n) time. Do not call `std::lower_bound`,
`std::upper_bound`, `std::equal_range`, `std::binary_search`, `std::find` or
`std::partition_point`.

Examples: `a = [2, 4, 6, 8]`: `target = 6 → 2`; `target = 5 → -1`; `target = 2 → 0`.
