#include <vector>

int max_water(const std::vector<int>& h) {
    int i = 0, j = static_cast<int>(h.size()) - 1, best = 0;
    while (i < j) {
        const int lines = j - i + 1;
        const int level = h[i] < h[j] ? h[i] : h[j];
        if (level * lines > best) best = level * lines;
        if (h[i] < h[j]) ++i; else --j;
    }
    return best;
}
