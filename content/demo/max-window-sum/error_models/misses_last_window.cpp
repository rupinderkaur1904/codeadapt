#include <algorithm>
#include <vector>

// Error model: the sliding loop stops one step early, so the last window is never summed.
int max_window_sum(const std::vector<int>& a, int k) {
    int sum = 0;
    for (int i = 0; i < k; ++i) sum += a[i];
    int best = sum;
    for (int i = k; i < static_cast<int>(a.size()) - 1; ++i) {
        sum += a[i] - a[i - k];
        best = std::max(best, sum);
    }
    return best;
}
