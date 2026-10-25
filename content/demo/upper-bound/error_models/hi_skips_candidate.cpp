#include <vector>

// In a half-open loop, an element greater than the target at mid sets hi = mid - 1,
// discarding mid, which may itself be the answer.
int upper_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return lo;
}
