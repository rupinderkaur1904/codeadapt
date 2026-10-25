// cause: computes the floor square root of x - 1 "so that exact squares are excluded"
//        (specification of the bound), using a correct search.
// cause-skill: problem_specification
// compare-with: strict_square_test
int int_sqrt(int x) {
    const long long y = x == 0 ? 0 : static_cast<long long>(x) - 1;
    long long lo = 0, hi = y, ans = 0;
    while (lo <= hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid <= y) { ans = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return static_cast<int>(ans);
}
