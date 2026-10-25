#include <vector>

int max_water(const std::vector<int>& height) {
    std::size_t i = 0, j = height.size() - 1;
    long long best = 0;
    while (i < j) {
        const long long level = height[i] < height[j] ? height[i] : height[j];
        const long long area = level * static_cast<long long>(j - i);
        if (area > best) best = area;
        if (height[i] <= height[j]) ++i;
        else --j;
    }
    return static_cast<int>(best);
}
