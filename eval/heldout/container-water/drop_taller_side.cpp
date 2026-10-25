#include <vector>

int max_water(const std::vector<int>& h) {
    int i = 0, j = static_cast<int>(h.size()) - 1, best = 0;
    while (i < j) {
        const int level = h[i] < h[j] ? h[i] : h[j];
        if (level * (j - i) > best) best = level * (j - i);
        if (h[j] < h[i]) ++i; else --j;
    }
    return best;
}
