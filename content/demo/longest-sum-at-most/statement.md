Implement

```cpp
int longest_at_most(const std::vector<int>& a, int s);
```

All values in `a` are positive. Return the length of the longest stretch of **consecutive**
elements whose sum is **at most** `s`, or `0` if no single element fits.

Constraints: `1 <= a.size() <= 100000`, `1 <= a[i] <= 10^4`, `1 <= s <= 10^9`.

Your solution must run in O(n) time.

Examples: `a = [3, 1, 2, 1, 4, 2], s = 5 → 3`; `a = [2, 2, 2, 2], s = 6 → 3`.
