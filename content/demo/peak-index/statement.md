Implement

```cpp
int peak_index(const std::vector<int>& a);
```

`a` is not empty. It strictly increases and then strictly decreases; either part may be empty,
so `a` may be entirely increasing or entirely decreasing. Return the **index** of the largest
element.

Your solution must run in O(log n) time. Do not call `std::max_element`,
`std::lower_bound`, `std::upper_bound` or `std::partition_point`.

Examples: `a = [1, 4, 9, 7, 2] → 2`; `a = [3, 5, 8] → 2`; `a = [6, 2] → 0`.
