// Closed interval with a running answer, but loops while lo < hi, so the last remaining
// candidate is never checked.
int int_sqrt(int x) {
    long long lo = 0;
    long long hi = x;
    long long ans = 0;
    while (lo < hi) {
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
