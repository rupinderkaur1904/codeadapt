#include <vector>

// cause: closed-interval updates but hi starts at n - 2 "because a[hi] is compared with mid",
//        so the last element is outside the initial search range.
// cause-skill: search_space_boundaries (not declared for this problem)
// compare-with: closed_loop_lt
int rotated_search(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 2;
    if (hi < 0) hi = 0;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[lo] <= a[mid]) {
            if (a[lo] <= target && target < a[mid]) hi = mid - 1; else lo = mid + 1;
        } else {
            if (a[mid] < target && target <= a[hi]) lo = mid + 1; else hi = mid - 1;
        }
    }
    return -1;
}
