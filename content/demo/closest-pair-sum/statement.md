Implement

```cpp
int closest_pair_gap(const std::vector<int>& a, int target);
```

`a` is sorted in non-decreasing order. Over all pairs of **different positions** `i < j`, return
the smallest value of `|a[i] + a[j] - target|`.

Constraints: `2 <= a.size() <= 100000`, `-10^8 <= a[i], target <= 10^8`.

Your solution must run in O(n) time.

Examples: `a = [1, 3, 5, 8, 12], target = 14 → 1`; `a = [2, 4, 7, 11], target = 11 → 0`.
