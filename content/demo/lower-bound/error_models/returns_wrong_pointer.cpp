#include <vector>

// Correct closed-interval search, but returns hi instead of lo. On exit hi == lo - 1, so
// it returns the last index whose element is below the target, not the boundary.
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return hi;
}
