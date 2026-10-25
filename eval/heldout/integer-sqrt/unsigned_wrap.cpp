// Squares in 32-bit unsigned arithmetic, which wraps for large mid.
int int_sqrt(int x) {
    unsigned lo = 0, hi = static_cast<unsigned>(x), ans = 0;
    while (lo <= hi) {
        unsigned mid = lo + (hi - lo) / 2;
        if (mid * mid <= static_cast<unsigned>(x)) {
            ans = mid;
            lo = mid + 1;
        } else {
            if (mid == 0) break;
            hi = mid - 1;
        }
    }
    return static_cast<int>(ans);
}
