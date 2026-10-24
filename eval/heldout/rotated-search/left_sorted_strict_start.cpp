#include <vector>

// Two-step test on the left half that requires the target to be strictly above its start.
int rotated_search(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        bool left_sorted = a[mid] >= a[lo];
        if (left_sorted) {
            bool in_left = target > a[lo] && target < a[mid];
            if (in_left) hi = mid - 1; else lo = mid + 1;
        } else {
            bool in_right = target > a[mid] && target <= a[hi];
            if (in_right) lo = mid + 1; else hi = mid - 1;
        }
    }
    return -1;
}
