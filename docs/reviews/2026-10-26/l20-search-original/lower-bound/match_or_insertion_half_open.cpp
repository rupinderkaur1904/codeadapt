#include <vector>

// cause: the same reading as match_or_insertion_closed ("any copy, else the insertion
//        point"), written with the half-open loop. The code is the model's code; only the
//        stated cause differs.
// cause-skill: problem_specification
// compare-with: stops_at_first_match
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1; else hi = mid;
    }
    return lo;
}
