#include <vector>

// A 0 at mid sets lo = mid instead of mid + 1; with two candidates left and the answer on
// the right, the range never shrinks.
int first_true(const std::vector<int>& flags) {
    int lo = 0;
    int hi = static_cast<int>(flags.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    return lo;
}
