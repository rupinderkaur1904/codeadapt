// cause: running-answer search over [0, x] with hi = x - 1 ("x itself is never the root"),
//        so for x = 1 the answer 1 is outside the range (search-space boundary).
// cause-skill: search_space_boundaries
// compare-with: closed_loop_lt
int int_sqrt(int x) {
    long long lo = 0, hi = static_cast<long long>(x) - 1, ans = 0;
    while (lo <= hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid <= x) { ans = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return static_cast<int>(ans);
}
