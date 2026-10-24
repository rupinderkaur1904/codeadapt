#include <vector>

// For-loop form whose condition stops while two indices still differ.
int rotated_search(const std::vector<int>& a, int target) {
    for (int lo = 0, hi = static_cast<int>(a.size()) - 1; lo < hi;) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[lo] <= a[mid]) {
            if (target >= a[lo] && target < a[mid]) hi = mid - 1;
            else lo = mid + 1;
        } else {
            if (target > a[mid] && target <= a[hi]) lo = mid + 1;
            else hi = mid - 1;
        }
    }
    return -1;
}
