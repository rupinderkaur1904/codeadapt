#include <vector>

// cause: reads the task as "find an index of the smallest value" (specification) and writes
//        a binary search that walks downhill.
// cause-skill: problem_specification
// compare-with: swapped_direction
int peak_index(const std::vector<int>& a) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid + 1] < a[mid]) lo = mid + 1; else hi = mid;  // go where values fall
    }
    return lo;
}
