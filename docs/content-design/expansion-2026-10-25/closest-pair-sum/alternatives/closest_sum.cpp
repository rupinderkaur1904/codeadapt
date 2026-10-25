#include <climits>
#include <cstdlib>
#include <vector>

// Alternative (unmodelled) error: returns the closest sum instead of the gap.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    int best = INT_MAX, sum_best = 0;
    while (lo < hi) {
        const int sum = a[lo] + a[hi];
        if (std::abs(sum - target) < best) { best = std::abs(sum - target); sum_best = sum; }
        if (sum < target) ++lo; else if (sum > target) --hi; else return sum;
    }
    return sum_best;
}
