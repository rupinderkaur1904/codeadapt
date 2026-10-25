#include <vector>

// cause: correct closed-interval search with an answer variable, reported 1-based
//        (output contract).
// cause-skill: problem_specification (same skill as the model)
// compare-with: returns_one_past
int last_occurrence(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = -1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) { ans = mid; lo = mid + 1; }
        else if (a[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return ans == -1 ? -1 : ans + 1;
}
