Implement

```cpp
int first_true(const std::vector<int>& flags);
```

Every element of `flags` is 0 or 1, and all the 0s come before all the 1s. `flags` may be
empty, all 0s or all 1s. Return the index of the first 1. If there is no 1, return
`flags.size()`.

Your solution must run in O(log n) time. Do not call `std::lower_bound`,
`std::upper_bound`, `std::equal_range`, `std::partition_point` or `std::find`.

Examples: `flags = [0, 0, 1, 1, 1] → 2`; `flags = [0, 0, 0] → 3`; `flags = [1, 1] → 0`.
