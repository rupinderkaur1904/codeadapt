// The same half-open form, with the range capped at 46340 "to avoid overflow" instead of
// 46341, so the first r with r * r > x cannot be 46341.
int int_sqrt(int x) {
    long long lo = 0;
    long long hi = static_cast<long long>(x) + 1;
    if (hi > 46340) hi = 46340;
    while (lo < hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid > x) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    return static_cast<int>(lo - 1);
}
