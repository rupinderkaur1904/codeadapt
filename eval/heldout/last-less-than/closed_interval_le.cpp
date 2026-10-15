#include <vector>

// Closed interval that also accepts elements equal to the target.
int last_less_than(const std::vector<int>& a, int target) {
    int best = -1;
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) { best = mid; lo = mid + 1; } else { hi = mid - 1; }
    }
    return best;
}
