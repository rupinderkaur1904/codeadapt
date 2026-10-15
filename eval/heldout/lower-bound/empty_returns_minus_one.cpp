#include <vector>

// Correct except for a special case outside the error model space: empty input -> -1.
int lower_bound_index(const std::vector<int>& a, int target) {
    if (a.empty()) return -1;
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) lo = mid + 1; else hi = mid;
    }
    return lo;
}
