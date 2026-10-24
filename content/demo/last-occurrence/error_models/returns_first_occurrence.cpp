#include <vector>

// Uses the lower bound (first element >= target) and checks it, so it returns the first occurrence of the target, not the last.
int last_occurrence(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return (lo < static_cast<int>(a.size()) && a[lo] == target) ? lo : -1;
}
