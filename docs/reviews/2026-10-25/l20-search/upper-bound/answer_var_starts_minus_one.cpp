#include <vector>

// cause: searches only the indices of a, [0, n - 1], with an answer variable that starts at -1,
//        so the candidate a.size() is outside the searched range (search-space boundary).
// cause-skill: search_space_boundaries
// compare-with: none_sentinel
int upper_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = -1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] > target) { ans = mid; hi = mid - 1; } else { lo = mid + 1; }
    }
    return ans;
}
