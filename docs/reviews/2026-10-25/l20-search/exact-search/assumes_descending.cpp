#include <vector>

// cause: reads the array as sorted in decreasing order (specification) and writes a correct
//        search for that order.
// cause-skill: problem_specification
// compare-with: swapped_direction
int search_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] > target) lo = mid + 1; else hi = mid - 1;  // larger values come first
    }
    return -1;
}
