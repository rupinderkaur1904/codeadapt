#include <vector>

// cause: correct half-open search, then returns lo - 1 "because the loop overshoots by one"
//        (reasoning about the state at loop exit).
// cause-skill: loop_termination (contestable: the bank maps "returns the wrong end of the
//              final interval" to problem_specification, see returns_wrong_pointer)
// compare-with: returns_wrong_pointer
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) lo = mid + 1; else hi = mid;
    }
    return lo - 1;
}
