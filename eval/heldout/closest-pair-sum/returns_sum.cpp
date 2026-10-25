#include <climits>
#include <cstdlib>
#include <vector>

// Returns the closest sum instead of the gap.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int left = 0, right = static_cast<int>(a.size()) - 1, best = INT_MAX, sum = 0;
    while (left < right) {
        const int s = a[left] + a[right];
        if (std::abs(s - target) < best) { best = std::abs(s - target); sum = s; }
        if (s == target) break;
        if (s < target) ++left; else --right;
    }
    return sum;
}
