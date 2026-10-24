#include <vector>

// Closed-interval search: one half of [lo, hi] around mid is always sorted; search it if it can hold the target, else the other half.
int rotated_search(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[lo] <= a[mid]) {  // [lo, mid] is sorted
            if (a[lo] <= target && target < a[mid]) {
                hi = mid - 1;
            } else {
                lo = mid + 1;
            }
        } else {  // [mid, hi] is sorted
            if (a[mid] < target && target <= a[hi]) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
    }
    return -1;
}
