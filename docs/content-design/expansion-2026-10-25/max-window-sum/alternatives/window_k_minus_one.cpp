#include <algorithm>
#include <vector>

// Alternative (unmodelled) error: windows of k - 1 elements (k >= 2), k elements when k == 1.
int max_window_sum(const std::vector<int>& a, int k) {
    const int w = k > 1 ? k - 1 : 1;
    int sum = 0;
    for (int i = 0; i < w; ++i) sum += a[i];
    int best = sum;
    for (int i = w; i < static_cast<int>(a.size()); ++i) { sum += a[i] - a[i - w]; best = std::max(best, sum); }
    return best;
}
