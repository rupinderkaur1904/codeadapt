// Accepts mid only when mid * mid < x, so a perfect square's own root is never accepted.
int int_sqrt(int x) {
    long long lo = 0;
    long long hi = x;
    long long ans = 0;
    while (lo <= hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid < x) {
            ans = mid;
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return static_cast<int>(ans);
}
