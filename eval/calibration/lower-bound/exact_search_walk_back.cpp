#include <vector>

// Exact-match search that walks back to the first occurrence, but returns -1 when absent.
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) {
            while (mid > 0 && a[mid - 1] == target) --mid;
            return mid;
        }
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return -1;
}
