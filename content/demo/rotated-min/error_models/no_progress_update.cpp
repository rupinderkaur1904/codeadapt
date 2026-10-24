#include <vector>

// Sets lo = mid instead of mid + 1, so the range stops shrinking once hi == lo + 1.
int rotated_min_index(const std::vector<int>& a) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] > a[hi]) {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    return lo;
}
