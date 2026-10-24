#include <vector>

// Sets lo = mid instead of mid + 1, so the range stops shrinking when hi == lo + 1.
int upper_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    return lo;
}
