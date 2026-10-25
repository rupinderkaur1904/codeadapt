#include <climits>
#include <cstdlib>
#include <vector>

// Alternative (unmodelled) error: only checks neighbouring pairs.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int best = INT_MAX;
    for (std::size_t i = 1; i < a.size(); ++i) {
        const int g = std::abs(a[i - 1] + a[i] - target);
        if (g < best) best = g;
    }
    return best;
}
