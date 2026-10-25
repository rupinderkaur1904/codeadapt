Implement

```cpp
int max_profit(const std::vector<int>& prices);
```

`prices[i]` is the price of a share on day `i`. You may buy one share on one day and sell it on a
**later** day. Return the largest profit you can make. If no trade makes a profit, return `0`
(you may choose not to trade).

Constraints: `1 <= prices.size() <= 100000`, `1 <= prices[i] <= 10000`.

Your solution must run in O(n) time.

Examples: `prices = [7, 1, 5, 3, 6, 4] → 5`; `prices = [7, 6, 4, 3, 1] → 0`.
