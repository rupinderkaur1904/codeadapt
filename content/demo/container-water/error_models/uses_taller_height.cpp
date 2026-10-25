#include <algorithm>
#include <vector>

// Error model: the water level is the taller line, not the shorter one.
int max_water(const std::vector<int>& height) {
    int lo = 0, hi = static_cast<int>(height.size()) - 1, best = 0;
    while (lo < hi) {
        best = std::max(best, std::max(height[lo], height[hi]) * (hi - lo));
        if (height[lo] < height[hi]) ++lo;
        else --hi;
    }
    return best;
}
