#include <vector>

// cause: finds the rotation point, then reports the target's rank in sorted order rather than
//        its index in a (specification).
// cause-skill: problem_specification (same skill as the model)
// compare-with: returns_sorted_position
int rotated_search(const std::vector<int>& a, int target) {
    const int n = static_cast<int>(a.size());
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] > a[hi]) lo = mid + 1; else hi = mid;
    }
    const int k = lo;
    for (int r = 0; r < n; ++r) if (a[(k + r) % n] == target) return r;
    return -1;
}
