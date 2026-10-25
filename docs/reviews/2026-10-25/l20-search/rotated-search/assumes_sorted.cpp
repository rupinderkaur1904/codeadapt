#include <vector>

// cause: does not register that the array is rotated (specification) and writes a correct
//        half-open lower-bound search.
// cause-skill: problem_specification (same skill as the model)
// compare-with: ignores_rotation
int rotated_search(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) lo = mid + 1; else hi = mid;
    }
    return (lo < static_cast<int>(a.size()) && a[lo] == target) ? lo : -1;
}
