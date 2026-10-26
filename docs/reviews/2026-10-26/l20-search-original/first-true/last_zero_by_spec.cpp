#include <vector>

// cause: task read as "the index of the last 0" (-1 if none); a correct search for that
//        reading.
// cause-skill: problem_specification
// compare-with: returns_last_false
int first_true(const std::vector<int>& flags) {
    int lo = 0, hi = static_cast<int>(flags.size()) - 1, ans = -1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) { ans = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return ans;
}
