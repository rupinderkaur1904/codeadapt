#include <cstdlib>
#include <vector>

// Uses the two tallest lines.
int max_water(const std::vector<int>& h) {
    int a = 0;
    for (int i = 1; i < static_cast<int>(h.size()); ++i) if (h[i] > h[a]) a = i;
    int b = a == 0 ? 1 : 0;
    for (int i = 0; i < static_cast<int>(h.size()); ++i) if (i != a && h[i] > h[b]) b = i;
    return (h[a] < h[b] ? h[a] : h[b]) * std::abs(a - b);
}
