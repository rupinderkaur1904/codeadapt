#include <vector>

// cause: task read as "the position of the target if present (any copy), otherwise where it
//        would be inserted"; the textbook closed-interval search for that reading.
// cause-skill: problem_specification
// compare-with: stops_at_first_match
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1; else hi = mid - 1;
    }
    return lo;
}
