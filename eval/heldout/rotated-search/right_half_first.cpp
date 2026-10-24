#include <vector>

// Checks whether the right half is sorted first, then the left.
int rotated_search(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < a[hi]) {
            if (target > a[mid] && target <= a[hi]) lo = mid + 1;
            else hi = mid - 1;
        } else {
            if (target >= a[lo] && target < a[mid]) hi = mid - 1;
            else lo = mid + 1;
        }
    }
    return -1;
}
