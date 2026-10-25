#include <vector>

// cause: reads the task as "the first element that is at least the target" (specification),
//        written as a closed interval with an answer variable rather than a half-open search.
// cause-skill: problem_specification
// compare-with: lower_bound_confusion
int upper_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = static_cast<int>(a.size());
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] >= target) { ans = mid; hi = mid - 1; } else { lo = mid + 1; }
    }
    return ans;
}
