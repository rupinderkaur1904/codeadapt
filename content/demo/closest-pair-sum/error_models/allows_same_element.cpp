#include <climits>
#include <cstdlib>
#include <vector>

// Error model: loops while lo <= hi, so an element can be paired with itself.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    int best = INT_MAX;
    while (lo <= hi) {
        const int sum = a[lo] + a[hi];
        const int gap = std::abs(sum - target);
        if (gap < best) best = gap;
        if (sum < target) ++lo;
        else if (sum > target) --hi;
        else return 0;
    }
    return best;
}
