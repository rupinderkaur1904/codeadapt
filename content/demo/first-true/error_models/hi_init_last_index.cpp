#include <vector>

// Half-open loop, but hi starts at n - 1, so the answer n (no 1 present) is unreachable.
int first_true(const std::vector<int>& flags) {
    int lo = 0;
    int hi = static_cast<int>(flags.size()) - 1;
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
