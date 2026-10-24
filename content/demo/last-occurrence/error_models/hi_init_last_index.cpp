#include <vector>

// Initialises hi = n - 1 with a half-open loop, so the boundary n is unreachable and an occurrence at the last index is missed.
int last_occurrence(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return (lo > 0 && a[lo - 1] == target) ? lo - 1 : -1;
}
