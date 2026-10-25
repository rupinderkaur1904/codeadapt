#include <climits>
#include <cstdlib>
#include <vector>

// Alternative cause for allows_same_element: a double loop with j starting at i.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int best = INT_MAX;
    for (std::size_t i = 0; i < a.size() && i < 3000; ++i)
        for (std::size_t j = i; j < a.size(); ++j) {
            const int g = std::abs(a[i] + a[j] - target);
            if (g < best) best = g;
        }
    return best;
}
