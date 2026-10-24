// Closed interval with no running answer, returning lo, which ends one past the answer.
int int_sqrt(int x) {
    long long lo = 0;
    long long hi = x;
    while (lo <= hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid <= x) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return static_cast<int>(lo);
}
