#include <algorithm>
#include <vector>

// Error model: the best sum starts at 0, so when every window sum is negative 0 is returned.
int max_window_sum(const std::vector<int>& a, int k) {
    int sum = 0, best = 0;
    for (int i = 0; i < k; ++i) sum += a[i];
    best = std::max(best, sum);
    for (int i = k; i < static_cast<int>(a.size()); ++i) {
        sum += a[i] - a[i - k];
        best = std::max(best, sum);
    }
    return best;
}
