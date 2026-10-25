#include <vector>

// cause: reads the task as "the first index where target occurs" (specification) and
//        writes a correct lower-bound search for that task.
// cause-skill: problem_specification
// compare-with: returns_first_occurrence
int last_occurrence(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) lo = mid + 1; else hi = mid;
    }
    return (lo < static_cast<int>(a.size()) && a[lo] == target) ? lo : -1;
}
