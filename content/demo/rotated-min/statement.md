Implement

```cpp
int rotated_min_index(const std::vector<int>& a);
```

`a` was obtained by rotating a strictly increasing array: some prefix (possibly empty) was
moved to the end. `a` is not empty and its elements are distinct. Return the **index** of the
smallest element.

Your solution must run in O(log n) time. Do not call `std::min_element`, `std::lower_bound`,
`std::upper_bound` or `std::partition_point`.

Examples: `a = [4, 5, 1, 2, 3] → 2`; `a = [1, 2, 3, 4] → 0`; `a = [9, 3] → 1`.
