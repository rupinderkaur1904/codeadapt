#include <vector>

// cause: correct closed-interval loop, but returns hi when the loop exits instead of lo
//        (reasoning about the state at loop exit; as upper-bound closed_returns_hi).
// cause-skill: loop_termination (contestable: l20-search.md case 3)
// compare-with: returns_last_false
int first_true(const std::vector<int>& flags) {
    int lo = 0, hi = static_cast<int>(flags.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) lo = mid + 1; else hi = mid - 1;
    }
    return hi;
}
