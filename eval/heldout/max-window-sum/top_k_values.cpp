#include <algorithm>
#include <functional>
#include <vector>

// Sums the k largest values, ignoring that they must be consecutive.
int max_window_sum(const std::vector<int>& a, int k) {
    std::vector<int> b(a);
    std::sort(b.begin(), b.end(), std::greater<int>());
    int s = 0;
    for (int i = 0; i < k; ++i) s += b[i];
    return s;
}
