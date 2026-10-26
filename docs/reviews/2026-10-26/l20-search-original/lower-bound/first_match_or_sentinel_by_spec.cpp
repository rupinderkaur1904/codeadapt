#include <vector>

// cause: task read as "the first occurrence of the target, or -1 if absent"; a correct
//        lower bound followed by a presence check.
// cause-skill: problem_specification
// compare-with: exact_match_sentinel
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) lo = mid + 1; else hi = mid;
    }
    return lo < static_cast<int>(a.size()) && a[lo] == target ? lo : -1;
}
