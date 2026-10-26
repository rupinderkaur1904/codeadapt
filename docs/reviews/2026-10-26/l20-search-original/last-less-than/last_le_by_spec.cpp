#include <vector>

// cause: task read as "the last element less than or equal to the target"; a correct search
//        for that reading, with an answer variable.
// cause-skill: problem_specification
// compare-with: uses_le
int last_less_than(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = -1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) { ans = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return ans;
}
