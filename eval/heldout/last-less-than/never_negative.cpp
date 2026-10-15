#include <vector>

// Correct search, but the "not found" case is reported as index 0.
int last_less_than(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (a[mid] < target) lo = mid + 1; else hi = mid;
    }
    if (lo == 0) return 0;
    return lo - 1;
}
