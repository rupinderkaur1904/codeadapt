// Closed interval recording the smallest mid whose square reaches x.
int int_sqrt(int x) {
    long long lo = 0, hi = x, ans = x;
    while (lo <= hi) {
        long long mid = lo + (hi - lo) / 2;
        if (mid * mid >= x) {
            ans = mid;
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    return static_cast<int>(ans);
}
