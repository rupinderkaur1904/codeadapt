// Closed interval with a running answer whose top is capped at 46339 "to stay safe".
int int_sqrt(int x) {
    long long lo = 0, hi = x < 46339 ? x : 46339, ans = 0;
    while (lo <= hi) {
        long long mid = lo + (hi - lo) / 2;
        if (mid * mid <= x) {
            ans = mid;
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return static_cast<int>(ans);
}
