// cause: special-cases small inputs wrongly ("the root of 0 and 1 is 0") and searches
//        correctly otherwise (specification of edge values, not the search range).
// cause-skill: problem_specification
// compare-with: hi_excludes_x
int int_sqrt(int x) {
    if (x < 2) return 0;
    long long lo = 0, hi = x, ans = 0;
    while (lo <= hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid <= x) { ans = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return static_cast<int>(ans);
}
