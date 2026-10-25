#include <vector>

// cause: closed interval with an answer variable, but on a[mid] > target it records mid - 1
//        instead of mid (updates the answer from the wrong side of the boundary).
// cause-skill: search_space_boundaries
// compare-with: hi_skips_candidate
int upper_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = static_cast<int>(a.size());
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] > target) { ans = mid; hi = mid - 2; } else { lo = mid + 1; }
    }
    return ans;
}
