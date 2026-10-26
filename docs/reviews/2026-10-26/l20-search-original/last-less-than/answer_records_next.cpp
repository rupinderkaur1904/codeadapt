#include <vector>

// cause: closed interval with an answer variable, but records mid + 1 ("the next
//        candidate") when a[mid] < target, and starts it at 0.
// cause-skill: loop_termination / update rule (contestable, as integer-sqrt
//              answer_records_next, l20-search.md case 13)
// compare-with: returns_insertion_point
int last_less_than(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = 0;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) { ans = mid + 1; lo = mid + 1; } else hi = mid - 1;
    }
    return ans;
}
