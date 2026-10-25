// cause: closed interval with an answer variable, but records mid + 1 ("the next candidate")
//        when mid * mid <= x (update of the answer variable).
// cause-skill: loop_termination / update rule (not a declared skill here)
// compare-with: returns_lo_closed
int int_sqrt(int x) {
    long long lo = 0, hi = x, ans = 0;
    while (lo <= hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid <= x) { ans = mid + 1; lo = mid + 1; } else hi = mid - 1;
    }
    return static_cast<int>(ans);
}
