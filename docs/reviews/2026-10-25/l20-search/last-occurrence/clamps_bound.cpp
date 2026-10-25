#include <vector>

// cause: correct upper bound, then clamps it to the last index "to stay in range" before the
//        equality check (output-range reasoning, not the initial search range).
// cause-skill: problem_specification
// compare-with: hi_init_last_index
int last_occurrence(const std::vector<int>& a, int target) {
    const int n = static_cast<int>(a.size());
    int lo = 0, hi = n;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) lo = mid + 1; else hi = mid;
    }
    if (n > 0 && lo == n) lo = n - 1;
    return (lo > 0 && a[lo - 1] == target) ? lo - 1 : -1;
}
