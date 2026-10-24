#include <vector>

// Moves right only while a[mid] < target, so elements equal to the target end up on the
// right: returns the first element >= target (lower bound) instead of > target.
int upper_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
