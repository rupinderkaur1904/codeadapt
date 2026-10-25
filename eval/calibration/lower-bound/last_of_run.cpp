#include <vector>

// Finds the target, then walks right to the end of its run.
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    while (lo + 1 < static_cast<int>(a.size()) && a[lo] == target && a[lo + 1] == target) ++lo;
    return lo;
}
