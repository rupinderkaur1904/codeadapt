#include <climits>
#include <cstdlib>
#include <vector>

// Error model: moves the pointers the wrong way (hi when the sum is too small, lo when it is
// too large), so the sum moves away from the target.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    int best = INT_MAX;
    while (lo < hi) {
        const int sum = a[lo] + a[hi];
        const int gap = std::abs(sum - target);
        if (gap < best) best = gap;
        if (sum < target) --hi;
        else if (sum > target) ++lo;
        else return 0;
    }
    return best;
}
