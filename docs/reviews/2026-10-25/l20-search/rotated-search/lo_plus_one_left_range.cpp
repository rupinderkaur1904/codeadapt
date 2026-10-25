#include <vector>

// cause: treats a[lo] as already examined, so the sorted left half is taken as (lo, mid)
//        rather than [lo, mid) (search-space boundary of the half, not the comparison).
// cause-skill: search_space_boundaries (not declared for this problem)
// compare-with: left_range_excludes_lo
int rotated_search(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[lo] <= a[mid]) {
            const bool in_left = lo + 1 <= mid - 1 && a[lo + 1] <= target && target < a[mid];
            if (in_left) hi = mid - 1; else lo = mid + 1;
        } else {
            if (a[mid] < target && target <= a[hi]) lo = mid + 1; else hi = mid - 1;
        }
    }
    return -1;
}
