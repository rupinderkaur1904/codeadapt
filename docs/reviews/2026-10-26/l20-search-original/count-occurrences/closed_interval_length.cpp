#include <vector>

// cause: counts the positions of the closed interval [first >= target, first > target],
//        i.e. treats the count as an inclusive length; boundaries found with answer
//        variables.
// cause-skill: problem_specification
// compare-with: inclusive_count
namespace {
int first_where(const std::vector<int>& a, int target, bool strict) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = static_cast<int>(a.size());
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (strict ? a[mid] > target : a[mid] >= target) { ans = mid; hi = mid - 1; }
        else lo = mid + 1;
    }
    return ans;
}
}  // namespace
int count_occurrences(const std::vector<int>& a, int target) {
    return first_where(a, target, true) - first_where(a, target, false) + 1;
}
