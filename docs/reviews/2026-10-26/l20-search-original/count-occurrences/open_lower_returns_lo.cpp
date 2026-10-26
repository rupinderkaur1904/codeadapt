#include <vector>

// cause: open-interval template (lo = -1, hi = n, answer in hi) for the lower boundary, but
//        returns lo instead of hi; the upper boundary is correct.
// cause-skill: problem_specification (the wrong end of the final interval; the bank maps that
//              cause to problem_specification in lower-bound returns_wrong_pointer)
// compare-with: inclusive_count
namespace {
int boundary(const std::vector<int>& a, int target, bool strict, bool return_lo) {
    int lo = -1, hi = static_cast<int>(a.size());
    while (hi - lo > 1) {
        const int mid = lo + (hi - lo) / 2;
        if (strict ? a[mid] <= target : a[mid] < target) lo = mid; else hi = mid;
    }
    return return_lo ? lo : hi;
}
}  // namespace
int count_occurrences(const std::vector<int>& a, int target) {
    return boundary(a, target, true, false) - boundary(a, target, false, true);
}
