#include <vector>

// Correct search, but returns -1 when there is no 1 (an exact-search habit).
int first_true(const std::vector<int>& flags) {
    const int n = static_cast<int>(flags.size());
    int lo = 0;
    int hi = n;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo == n ? -1 : lo;
}
