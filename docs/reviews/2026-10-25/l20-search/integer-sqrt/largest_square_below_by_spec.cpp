// cause: reads the task as "the largest r whose square is below x" (specification), written
//        as a half-open search for the first r with r * r >= x, minus one.
// cause-skill: problem_specification
// compare-with: strict_square_test
int int_sqrt(int x) {
    long long lo = 0, hi = static_cast<long long>(x) + 1;
    while (lo < hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid >= x) hi = mid; else lo = mid + 1;
    }
    return lo == 0 ? 0 : static_cast<int>(lo - 1);
}
