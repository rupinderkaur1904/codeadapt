// Closed-interval search that returns hi (the last index below the boundary) instead of lo.
#include <vector>

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
