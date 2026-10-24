// Returns the smallest r with r * r >= x (the ceiling of the square root), a lower-bound
// habit, instead of the floor.
int int_sqrt(int x) {
    long long lo = 0;
    long long hi = static_cast<long long>(x) + 1;
    while (lo < hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid >= x) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    return static_cast<int>(lo);
}
