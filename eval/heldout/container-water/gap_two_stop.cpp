#include <algorithm>
#include <vector>

int max_water(const std::vector<int>& h) {
    int best = 0;
    for (int i = 0, j = static_cast<int>(h.size()) - 1; j - i > 1;) {
        best = std::max(best, std::min(h[i], h[j]) * (j - i));
        if (h[i] < h[j]) ++i; else --j;
    }
    return best;
}
