Implement

```cpp
int rotated_search(const std::vector<int>& a, int target);
```

`a` was obtained by rotating a strictly increasing array: some prefix (possibly empty) was
moved to the end. `a` is not empty and its elements are distinct. Return the index `i` with
`a[i] == target`, or -1 if `target` does not occur.

Your solution must run in O(log n) time. Do not call `std::find`, `std::lower_bound`,
`std::upper_bound`, `std::binary_search` or `std::partition_point`.

Examples: `a = [4, 5, 6, 1, 2, 3], target = 2 → 4`; `a = [4, 5, 6, 1, 2, 3], target = 7 → -1`.
