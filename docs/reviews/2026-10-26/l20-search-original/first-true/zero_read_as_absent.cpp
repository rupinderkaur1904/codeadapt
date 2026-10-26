#include <vector>

// cause: correct search, but a result of 0 is treated as "not found" and replaced by 1. No
//        plausible reading of the task gives this; it is written only to test whether
//        lo_init_one's behaviour has any other program.
// cause-skill: problem_specification (unsupported: no plausible cause)
// compare-with: lo_init_one
int first_true(const std::vector<int>& flags) {
    int lo = 0, hi = static_cast<int>(flags.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) lo = mid + 1; else hi = mid;
    }
    return lo == 0 ? 1 : lo;
}
