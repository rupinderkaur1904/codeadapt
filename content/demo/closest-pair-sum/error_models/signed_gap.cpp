#include <climits>
#include <cstdlib>
#include <vector>

// Error model: returns the signed difference (sum - target) of the closest pair instead of its
// absolute value.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    int best = INT_MAX, best_signed = 0;
    while (lo < hi) {
        const int sum = a[lo] + a[hi];
        if (std::abs(sum - target) < best) {
            best = std::abs(sum - target);
            best_signed = sum - target;
        }
        if (sum < target) ++lo;
        else if (sum > target) --hi;
        else return 0;
    }
    return best_signed;
}
