// "Last true" form with lo = mid and a floor midpoint: once hi == lo + 1 and lo is valid,
// mid == lo and the range never shrinks.
int int_sqrt(int x) {
    long long lo = 0;
    long long hi = x;
    while (lo < hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid <= x) {
            lo = mid;
        } else {
            hi = mid - 1;
        }
    }
    return static_cast<int>(lo);
}
