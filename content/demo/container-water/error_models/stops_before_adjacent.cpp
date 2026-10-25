#include <algorithm>
#include <vector>

// Error model: loops while lo + 1 < hi, so the last pair (neighbouring lines) is never checked.
int max_water(const std::vector<int>& height) {
    int lo = 0, hi = static_cast<int>(height.size()) - 1, best = 0;
    while (lo + 1 < hi) {
        best = std::max(best, std::min(height[lo], height[hi]) * (hi - lo));
        if (height[lo] < height[hi]) ++lo;
        else --hi;
    }
    return best;
}
