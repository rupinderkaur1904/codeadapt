#include <vector>

// cause: closed-interval updates (hi = mid - 1) with a loop that stops while one candidate
//        is left (lo < hi), returning lo unchecked.
// cause-skill: loop_termination
// compare-with: hi_skips_candidate
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    if (hi < 0) return 0;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) lo = mid + 1; else hi = mid - 1;
    }
    return a[lo] < target ? lo + 1 : lo;
}
