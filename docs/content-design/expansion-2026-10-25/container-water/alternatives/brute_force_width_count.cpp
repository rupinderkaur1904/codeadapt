#include <algorithm>
#include <vector>

// Alternative cause for width_plus_one: a double loop (small n only) counting lines.
int max_water(const std::vector<int>& height) {
    int best = 0;
    const int n = static_cast<int>(height.size());
    for (int i = 0; i < n && i < 3000; ++i)
        for (int j = i + 1; j < n; ++j) best = std::max(best, std::min(height[i], height[j]) * (j - i + 1));
    return best;
}
