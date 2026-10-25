#include <vector>

// Closed-interval loop (lo <= hi, hi starting at n - 1) with the half-open update
// hi = mid: once lo == hi and a[mid] >= target, nothing changes and the loop never ends.
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
