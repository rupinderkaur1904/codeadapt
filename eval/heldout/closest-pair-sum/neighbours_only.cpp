#include <climits>
#include <cstdlib>
#include <vector>

// Only checks neighbouring pairs.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int best = INT_MAX;
    for (std::size_t i = 0; i + 1 < a.size(); ++i) {
        const int g = std::abs(a[i] + a[i + 1] - target);
        if (g < best) best = g;
    }
    return best;
}
