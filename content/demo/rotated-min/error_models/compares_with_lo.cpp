#include <vector>

// Compares the midpoint with the first element of the range instead of the last, which discards the minimum when the range is not rotated.
int rotated_min_index(const std::vector<int>& a) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] >= a[lo]) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
