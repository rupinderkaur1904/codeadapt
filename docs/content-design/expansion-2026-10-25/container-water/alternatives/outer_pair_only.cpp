#include <algorithm>
#include <vector>

// Alternative (unmodelled) error: only the outermost pair.
int max_water(const std::vector<int>& height) {
    return std::min(height.front(), height.back()) * (static_cast<int>(height.size()) - 1);
}
