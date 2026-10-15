Implement

```cpp
int count_occurrences(const std::vector<int>& a, int target);
```

`a` is sorted in non-decreasing order and may be empty. Return how many elements of `a`
equal `target`.

Your solution must run in O(log n) time, so you cannot scan the array. Do not call
`std::lower_bound`, `std::upper_bound`, `std::equal_range` or `std::count`.

Examples: `a = [1, 2, 2, 2, 5]`: `target = 2 → 3`; `target = 3 → 0`; `target = 5 → 1`.
