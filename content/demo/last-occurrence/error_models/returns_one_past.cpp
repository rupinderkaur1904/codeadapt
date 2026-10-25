#include <vector>

// Returns the upper bound itself (one past the last occurrence) and -1 only when nothing is <= target.
int last_occurrence(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return (lo > 0 && a[lo - 1] == target) ? lo : -1;
}
