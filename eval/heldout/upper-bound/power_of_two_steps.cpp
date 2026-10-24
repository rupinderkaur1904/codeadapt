#include <vector>

// Decreasing power-of-two jumps over the elements <= target.
int upper_bound_index(const std::vector<int>& a, int target) {
    const int n = static_cast<int>(a.size());
    int pos = -1;
    int step = 1;
    while (step * 2 <= n) step *= 2;
    for (; step > 0; step /= 2) {
        if (pos + step < n && a[pos + step] <= target) pos += step;
    }
    return pos + 1;
}
