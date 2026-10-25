Implement

```cpp
int remove_duplicates(std::vector<int>& a);
```

`a` is sorted in non-decreasing order. Rearrange it **in place** so that its first `k` elements
are the distinct values of `a`, in increasing order, and return `k`. What is left after position
`k` does not matter.

Constraints: `1 <= a.size() <= 100000`, `-10^9 <= a[i] <= 10^9`.

Your solution must run in O(n) time and use O(1) extra memory. Do not call `std::unique`.

Examples: `[1, 1, 2, 3, 3, 3, 4] → 4`, with `a` starting `[1, 2, 3, 4]`;
`[4, 5, 6] → 3`.
