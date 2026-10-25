#include <algorithm>
#include <vector>

// Alternative (unmodelled) error: uses the two tallest lines.
int max_water(const std::vector<int>& height) {
    int a = 0;
    for (int i = 1; i < static_cast<int>(height.size()); ++i) if (height[i] > height[a]) a = i;
    int b = a == 0 ? 1 : 0;
    for (int i = 0; i < static_cast<int>(height.size()); ++i) if (i != a && height[i] > height[b]) b = i;
    return std::min(height[a], height[b]) * std::abs(a - b);
}
