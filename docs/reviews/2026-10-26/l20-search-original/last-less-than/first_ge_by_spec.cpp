#include <vector>

// cause: task read as "the first element not less than the target" (n if none); a correct
//        search for that reading.
// cause-skill: problem_specification
// compare-with: returns_insertion_point
int last_less_than(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = static_cast<int>(a.size());
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] >= target) { ans = mid; hi = mid - 1; } else lo = mid + 1;
    }
    return ans;
}
