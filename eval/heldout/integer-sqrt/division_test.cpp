// Compares mid with x / mid instead of squaring, so no 64-bit product is needed.
int int_sqrt(int x) {
    if (x < 2) return x;
    int lo = 1, hi = x / 2, best = 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (mid <= x / mid) {
            best = mid;
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return best;
}
