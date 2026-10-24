// Tests the "too big" case first; equality falls into the too-big branch.
int int_sqrt(int x) {
    long long lo = 0, hi = x, ans = 0;
    while (lo <= hi) {
        long long mid = (lo + hi) >> 1;
        if (mid * mid >= x) {
            hi = mid - 1;
        } else {
            ans = mid;
            lo = mid + 1;
        }
    }
    return static_cast<int>(ans);
}
