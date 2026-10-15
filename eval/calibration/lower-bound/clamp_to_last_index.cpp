#include <vector>

// Correct half-open search, then "keeps the index valid" by clamping n to n - 1.
int lower_bound_index(const std::vector<int>& a, int target) {
    const int n = static_cast<int>(a.size());
    int lo = 0;
    int hi = n;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo < n ? lo : n - 1;
}
