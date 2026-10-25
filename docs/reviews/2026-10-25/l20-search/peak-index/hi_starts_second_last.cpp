#include <vector>

// cause: hi starts at n - 2 "so that a[mid + 1] is always in range", so the last index is
//        never a candidate (search-space boundary).
// cause-skill: search_space_boundaries
// compare-with: stops_one_early
int peak_index(const std::vector<int>& a) {
    int lo = 0, hi = static_cast<int>(a.size()) - 2;
    if (hi < 0) return 0;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < a[mid + 1]) lo = mid + 1; else hi = mid;
    }
    return lo;
}
