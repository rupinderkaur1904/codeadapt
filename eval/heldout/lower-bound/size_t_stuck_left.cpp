#include <cstddef>
#include <vector>

// Unsigned half-open search written with an explicit break; the left update keeps `half`
// instead of moving past it.
int lower_bound_index(const std::vector<int>& a, int target) {
    std::size_t first = 0;
    std::size_t last = a.size();
    for (;;) {
        if (first >= last) break;
        std::size_t half = first + (last - first) / 2;
        if (a[half] < target)
            first = half;
        else
            last = half;
    }
    return static_cast<int>(first);
}
