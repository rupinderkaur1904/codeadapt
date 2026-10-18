#include <vector>

// Half-open loop, but a 1 at mid sets hi = mid - 1, discarding flags[mid], which may itself
// be the answer.
int first_true(const std::vector<int>& flags) {
    int lo = 0;
    int hi = static_cast<int>(flags.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return lo;
}
