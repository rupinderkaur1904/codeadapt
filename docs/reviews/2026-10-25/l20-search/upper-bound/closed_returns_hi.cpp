#include <vector>

// cause: correct closed-interval loop, but returns hi when the loop exits instead of lo
//        (reasoning about the state at loop exit).
// cause-skill: loop_termination (contestable: also a problem_specification reading)
// compare-with: returns_last_not_greater
int upper_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) lo = mid + 1; else hi = mid - 1;
    }
    return hi;
}
