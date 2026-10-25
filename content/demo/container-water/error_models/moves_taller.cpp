#include <algorithm>
#include <vector>

// Error model: moves the pointer at the taller line, discarding the line that could still form
// a larger container.
int max_water(const std::vector<int>& height) {
    int lo = 0, hi = static_cast<int>(height.size()) - 1, best = 0;
    while (lo < hi) {
        best = std::max(best, std::min(height[lo], height[hi]) * (hi - lo));
        if (height[lo] > height[hi]) ++lo;
        else --hi;
    }
    return best;
}
