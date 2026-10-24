#include <vector>

// Returns -1 instead of a.size() when no element is greater than the target.
int upper_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo == static_cast<int>(a.size()) ? -1 : lo;
}
