#include <vector>

// cause: task read as "the last element below the target" (-1 if none); a correct search
//        for that reading, with an answer variable.
// cause-skill: problem_specification
// compare-with: returns_wrong_pointer
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = -1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) { ans = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return ans;
}
