Implement

```cpp
int int_sqrt(int x);
```

`0 <= x <= 2^31 - 1`. Return the integer square root of `x`: the largest `r` with
`r * r <= x` (that is, `floor(sqrt(x))`, which is at most 46340).

Compute `r * r` in 64-bit arithmetic (`long long`): `46341 * 46341` does not fit in an `int`.

Your solution must run in O(log x) time. Do not call `sqrt`, `sqrtf`, `sqrtl`, `pow`, `cbrt`
or `hypot`.

Examples: `x = 8 → 2`; `x = 16 → 4`; `x = 0 → 0`.
