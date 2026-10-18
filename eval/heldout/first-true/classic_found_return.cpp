#include <vector>

// Textbook "found it" binary search over a closed interval, applied to the flags.
int first_true(const std::vector<int>& flags) {
    int lo = 0, hi = static_cast<int>(flags.size()) - 1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        if (flags[mid] == 1) return mid;
        lo = mid + 1;
    }
    return static_cast<int>(flags.size());
}
