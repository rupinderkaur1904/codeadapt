#include <algorithm>
#include <vector>

// Error model: subtracts a[i - k + 1] instead of a[i - k], so the window drifts by one element.
int max_window_sum(const std::vector<int>& a, int k) {
    int sum = 0;
    for (int i = 0; i < k; ++i) sum += a[i];
    int best = sum;
    for (int i = k; i < static_cast<int>(a.size()); ++i) {
        sum += a[i] - a[i - k + 1];
        best = std::max(best, sum);
    }
    return best;
}
