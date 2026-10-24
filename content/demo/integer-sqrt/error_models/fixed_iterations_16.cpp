// Runs at most 16 iterations ("the answer is below 2^16") although the range is [0, x],
// so the search stops before the range is empty when x is large.
int int_sqrt(int x) {
    long long lo = 0;
    long long hi = x;
    long long ans = 0;
    for (int i = 0; i < 16 && lo <= hi; ++i) {
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
