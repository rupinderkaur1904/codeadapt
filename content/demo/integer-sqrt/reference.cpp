// Closed interval [lo, hi] with a running answer: every mid with mid * mid <= x is a
// candidate; the largest one seen is the answer.
int int_sqrt(int x) {
    long long lo = 0;
    long long hi = x;
    long long ans = 0;
    while (lo <= hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid <= x) {
            ans = mid;
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return static_cast<int>(ans);
}
