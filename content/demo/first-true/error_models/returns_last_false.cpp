#include <vector>

// Correct search, but returns the index of the last 0 (lo - 1) instead of the first 1.
int first_true(const std::vector<int>& flags) {
    int lo = 0;
    int hi = static_cast<int>(flags.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo - 1;
}
