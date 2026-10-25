#include <vector>

// Correct search that reports a 1-based position (and 0 when absent).
int last_occurrence(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) lo = mid + 1;
        else hi = mid;
    }
    return (lo > 0 && a[lo - 1] == target) ? lo : 0;
}
