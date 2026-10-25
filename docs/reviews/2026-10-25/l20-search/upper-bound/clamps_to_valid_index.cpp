#include <vector>

// cause: correct search, then believes the result must be a valid index into a, so an
//        answer of a.size() is clamped to the last index (specification of the output).
// cause-skill: problem_specification
// compare-with: hi_init_last_index
int upper_bound_index(const std::vector<int>& a, int target) {
    const int n = static_cast<int>(a.size());
    int lo = 0, hi = n;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) lo = mid + 1; else hi = mid;
    }
    if (n > 0 && lo == n) return n - 1;
    return lo;
}
