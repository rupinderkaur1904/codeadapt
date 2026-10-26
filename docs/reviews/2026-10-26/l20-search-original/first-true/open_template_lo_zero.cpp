#include <vector>

// cause: open-interval template (lo = -1, hi = n, answer in hi) with lo initialised to 0, so
//        index 0 is treated as known to be 0.
// cause-skill: search_space_boundaries
// compare-with: stops_one_early
int first_true(const std::vector<int>& flags) {
    int lo = 0, hi = static_cast<int>(flags.size());
    while (hi - lo > 1) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) lo = mid; else hi = mid;
    }
    return hi;
}
