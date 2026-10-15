#include <vector>

// Returns how many elements are below the target instead of the last such index.
int last_less_than(const std::vector<int>& a, int target) {
    int below = 0;
    int width = static_cast<int>(a.size());
    while (width > 0) {
        int half = width / 2;
        if (a[below + half] < target) { below += half + 1; width -= half + 1; } else { width = half; }
    }
    return below;
}
