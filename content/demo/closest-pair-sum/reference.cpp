#include <climits>
#include <cstdlib>
#include <vector>

// Two pointers from both ends: a sum below the target can only grow by moving `lo` right, a
// sum above it can only shrink by moving `hi` left. Only pairs with lo < hi are considered.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    int best = INT_MAX;
    while (lo < hi) {
        const int sum = a[lo] + a[hi];
        const int gap = std::abs(sum - target);
        if (gap < best) best = gap;
        if (sum < target) ++lo;
        else if (sum > target) --hi;
        else return 0;
    }
    return best;
}
