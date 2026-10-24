// For-loop form with a best-so-far variable; the loop runs while left < right.
int int_sqrt(int x) {
    long long left = 0, right = x, best = 0;
    for (; left < right;) {
        long long m = (left + right) / 2;
        if (m * m <= x) {
            best = m;
            left = m + 1;
        } else {
            right = m - 1;
        }
    }
    return static_cast<int>(best);
}
