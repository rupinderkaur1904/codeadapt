#include <vector>

// cause: half-open bounds but a closed-interval loop condition (lo <= hi guarded) with
//        hi = mid - 1 on a 1, so the first 1 can be stepped over.
// cause-skill: loop_termination
// compare-with: hi_skips_candidate
int first_true(const std::vector<int>& flags) {
    int lo = 0, hi = static_cast<int>(flags.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) lo = mid + 1; else { if (mid == lo) return mid; hi = mid - 1; }
    }
    return lo;
}
