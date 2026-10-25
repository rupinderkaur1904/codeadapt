#include <vector>

// cause: correct search, but uses the result as a truth value, so index 0 is reported as
//        "not found" (output contract / specification, not the search range).
// cause-skill: problem_specification
// compare-with: lo_init_one
static int find(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1; else hi = mid - 1;
    }
    return 0;
}
int search_index(const std::vector<int>& a, int target) {
    const int r = find(a, target);
    return r ? r : -1;
}
