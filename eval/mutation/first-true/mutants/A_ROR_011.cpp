#include <vector>

// Half-open search space [lo, hi); invariant: flags[i] == 0 for i < lo, flags[i] == 1 for i >= hi.
int first_true(const std::vector<int>& flags) {
    int lo = 0;
    int hi = static_cast<int>(flags.size());
    while (lo != hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
