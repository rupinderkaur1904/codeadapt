#include <vector>

// lo starts at 1 (a 1-based habit), so index 0 is never a candidate.
int first_true(const std::vector<int>& flags) {
    int lo = 1;
    int hi = static_cast<int>(flags.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
