#include <climits>
#include <cstdlib>
#include <vector>

// Error model: the left pointer starts at index 1, so pairs using a[0] are never considered.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int lo = 1, hi = static_cast<int>(a.size()) - 1;
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
