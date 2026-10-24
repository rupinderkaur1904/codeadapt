#include <vector>

// Compares the midpoint with the last element of the range: if it is larger, the minimum lies to its right.
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
    return lo;
}
