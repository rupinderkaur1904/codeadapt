#include <vector>

// Returns as soon as flags[mid] == 1, which finds some 1 but not necessarily the first.
int first_true(const std::vector<int>& flags) {
    int lo = 0;
    int hi = static_cast<int>(flags.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 1) {
            return mid;
        }
        lo = mid + 1;
    }
    return lo;
}
