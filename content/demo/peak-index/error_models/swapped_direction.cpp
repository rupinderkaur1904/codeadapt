#include <vector>

// Moves the wrong way: a rising step at mid discards the right half, which holds the peak.
int peak_index(const std::vector<int>& a) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] > a[mid + 1]) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
