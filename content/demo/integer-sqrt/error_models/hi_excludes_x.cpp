// Half-open search for the first r with r * r > x, minus one, but with hi = x instead of
// x + 1, so the candidate r = x is never in range.
int int_sqrt(int x) {
    long long lo = 0;
    long long hi = x;
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
