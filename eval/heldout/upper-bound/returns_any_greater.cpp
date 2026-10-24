#include <vector>

// Returns as soon as it lands on an element greater than the target whose left neighbour
// is also greater, so it can stop past the first greater element.
int upper_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] > target) {
            if (mid == 0 || a[mid - 1] > target) return mid;
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    return lo;
}
