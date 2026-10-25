#include <vector>

// cause: half-open loop with hi initialised to n - 1, so the last element is never examined
//        (search-space boundary, not the loop condition).
// cause-skill: search_space_boundaries
// compare-with: closed_loop_lt
int search_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1; else hi = mid;
    }
    return -1;
}
