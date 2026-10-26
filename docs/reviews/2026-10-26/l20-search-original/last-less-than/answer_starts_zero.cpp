#include <vector>

// cause: closed-interval search with an answer variable initialised to 0 instead of -1, so
//        the answer -1 is unreachable (the same classification as upper-bound
//        answer_var_starts_minus_one, l20-search.md case 4).
// cause-skill: search_space_boundaries
// compare-with: clamps_to_zero
int last_less_than(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = 0;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) { ans = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return ans;
}
