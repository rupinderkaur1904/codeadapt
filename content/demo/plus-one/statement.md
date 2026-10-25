Implement

```cpp
std::vector<int> plus_one(const std::vector<int>& digits);
```

`digits` holds a non-negative integer, one decimal digit per element, **most significant digit
first**, with no leading zero (except for the number 0 itself). Return the digits of the number
plus one, in the same format.

Constraints: `1 <= digits.size() <= 100000`, `0 <= digits[i] <= 9`.

Your solution must run in O(n) time. The number can be far too large for any built-in integer
type.

Examples: `[1, 2, 3] → [1, 2, 4]`; `[1, 2, 9, 9] → [1, 3, 0, 0]`; `[9, 9] → [1, 0, 0]`.
