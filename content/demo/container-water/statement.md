Implement

```cpp
int max_water(const std::vector<int>& height);
```

Line `i` is drawn at position `i` with height `height[i]`. Two lines at positions `i < j` form a
container whose water level is the **shorter** of the two lines and whose width is `j - i`.
Return the largest amount of water any container can hold (level × width).

Constraints: `2 <= height.size() <= 100000`, `0 <= height[i] <= 10000`.

Your solution must run in O(n) time.

Examples: `[1, 8, 6, 2, 5, 4, 8, 3, 7] → 49`; `[1, 1] → 1`.
