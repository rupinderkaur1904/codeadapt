Implement

```cpp
int first_max_index(const std::vector<int>& a);
```

Return the index (0-based) of the largest value in `a`. If the largest value occurs more than
once, return the **smallest** such index.

Constraints: `1 <= a.size() <= 100000`, `-10^9 <= a[i] <= 10^9`.

Your solution must run in O(n) time. Do not call `std::max_element`.

Examples: `a = [3, 9, 2, 9, 5, 1] → 1`; `a = [1, 2, 3, 7] → 3`.
