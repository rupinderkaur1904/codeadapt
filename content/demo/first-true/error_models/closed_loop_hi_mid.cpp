#include <vector>

// Closed range [lo, hi] with loop condition lo <= hi, but a 1 at mid sets hi = mid: once
// lo == hi on a 1, the range never shrinks.
int first_true(const std::vector<int>& flags) {
    int lo = 0;
    int hi = static_cast<int>(flags.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
