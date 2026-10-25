Implement

```cpp
int second_largest(const std::vector<int>& a);
```

Return the largest value in `a` that is **strictly smaller** than the maximum of `a`. If no such
value exists (every element is equal), return `-1`.

Constraints: `1 <= a.size() <= 100000`, `0 <= a[i] <= 10^9`.

Your solution must run in O(n) time.

Examples: `a = [4, 9, 2, 9, 7, 1] → 7`; `a = [5, 5, 5] → -1`.
