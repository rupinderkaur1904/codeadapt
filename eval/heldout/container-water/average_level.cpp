#include <algorithm>
#include <vector>

// Uses the average of the two heights as the level.
int max_water(const std::vector<int>& h) {
    int i = 0, j = static_cast<int>(h.size()) - 1, best = 0;
    while (i < j) {
        best = std::max(best, (h[i] + h[j]) / 2 * (j - i));
        if (h[i] < h[j]) ++i; else --j;
    }
    return best;
}
