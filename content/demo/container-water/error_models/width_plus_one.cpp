#include <algorithm>
#include <vector>

// Error model: counts the width as hi - lo + 1 (the number of lines), not the distance.
int max_water(const std::vector<int>& height) {
    int lo = 0, hi = static_cast<int>(height.size()) - 1, best = 0;
    while (lo < hi) {
        best = std::max(best, std::min(height[lo], height[hi]) * (hi - lo + 1));
        if (height[lo] < height[hi]) ++lo;
        else --hi;
    }
    return best;
}
