#include <vector>

// cause: task read as "first element greater than the target"; a correct search for that
//        reading, written with an answer variable.
// cause-skill: problem_specification
// compare-with: upper_bound_confusion
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = static_cast<int>(a.size());
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] > target) { ans = mid; hi = mid - 1; } else lo = mid + 1;
    }
    return ans;
}
