#include <vector>

// cause: computes the lower bound and forgets the absence check (specification).
// cause-skill: problem_specification (same skill as the model)
// compare-with: returns_insertion_point
int search_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) lo = mid + 1; else hi = mid;
    }
    return lo;
}
