#include <algorithm>
#include <vector>

// Moves the shorter side past every line that is not taller than it.
int max_water(const std::vector<int>& h) {
    int i = 0, j = static_cast<int>(h.size()) - 1, best = 0;
    while (i < j) {
        const int level = std::min(h[i], h[j]);
        best = std::max(best, level * (j - i));
        while (i < j && h[i] <= level) ++i;
        while (i < j && h[j] <= level) --j;
    }
    return best;
}
