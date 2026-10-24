#include <vector>

// Checks whether the left part [lo, mid] is in order, and if so moves right.
int rotated_min_index(const std::vector<int>& a) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        bool left_in_order = a[lo] <= a[mid];
        if (left_in_order) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
