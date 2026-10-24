#include <vector>

// Returns the index of the maximum (the element just before the minimum, cyclically) instead of the minimum.
int rotated_min_index(const std::vector<int>& a) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] > a[hi]) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return (lo + static_cast<int>(a.size()) - 1) % static_cast<int>(a.size());
}
