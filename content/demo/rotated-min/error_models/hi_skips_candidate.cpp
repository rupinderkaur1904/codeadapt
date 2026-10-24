#include <vector>

// Sets hi = mid - 1 when the midpoint is not larger than the last element, which can discard the minimum itself.
int rotated_min_index(const std::vector<int>& a) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] > a[hi]) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return lo;
}
