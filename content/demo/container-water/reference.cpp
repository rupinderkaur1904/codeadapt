#include <algorithm>
#include <vector>

// Two pointers from both ends; the shorter line limits every container that uses it, so it is
// the one to move.
int max_water(const std::vector<int>& height) {
    int lo = 0, hi = static_cast<int>(height.size()) - 1, best = 0;
    while (lo < hi) {
        best = std::max(best, std::min(height[lo], height[hi]) * (hi - lo));
        if (height[lo] < height[hi]) ++lo;
        else --hi;
    }
    return best;
}
