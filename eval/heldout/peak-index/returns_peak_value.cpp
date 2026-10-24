#include <vector>

// Closed interval with a running answer, returning the element found.
int peak_index(const std::vector<int>& a) {
    int n = static_cast<int>(a.size());
    int lo = 0, hi = n - 1, best = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (mid + 1 < n && a[mid] < a[mid + 1]) {
            lo = mid + 1;
        } else {
            best = mid;
            hi = mid - 1;
        }
    }
    return a[best];
}
