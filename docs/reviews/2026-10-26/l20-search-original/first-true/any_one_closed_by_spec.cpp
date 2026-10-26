#include <vector>

// cause: task read as "the index of any 1" (n if none); the textbook closed-interval exact
//        search for a 1.
// cause-skill: problem_specification
// compare-with: returns_any_true
int first_true(const std::vector<int>& flags) {
    int lo = 0, hi = static_cast<int>(flags.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 1) return mid;
        lo = mid + 1;
    }
    return static_cast<int>(flags.size());
}
