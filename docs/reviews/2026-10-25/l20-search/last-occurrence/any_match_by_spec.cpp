#include <vector>

// cause: reads the task as "return an index where target occurs" (specification) and
//        writes a textbook exact search.
// cause-skill: problem_specification
// compare-with: stops_at_any_match
int last_occurrence(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1; else hi = mid - 1;
    }
    return -1;
}
