#include <vector>

// Correct search, but treats an empty array as an error and returns -1 for it only.
int first_true(const std::vector<int>& flags) {
    if (flags.empty()) return -1;
    int lo = 0, hi = flags.size();
    while (lo != hi) {
        int mid = (lo + hi) / 2;
        if (flags[mid] == 0) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
