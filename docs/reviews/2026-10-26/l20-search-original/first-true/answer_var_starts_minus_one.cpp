#include <vector>

// cause: closed-interval search over [0, n - 1] with the answer variable starting at -1, so
//        the answer n is unreachable (the classification of l20-search.md case 4).
// cause-skill: search_space_boundaries
// compare-with: none_sentinel
int first_true(const std::vector<int>& flags) {
    int lo = 0, hi = static_cast<int>(flags.size()) - 1, ans = -1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 1) { ans = mid; hi = mid - 1; } else lo = mid + 1;
    }
    return ans;
}
