#include <algorithm>
#include <vector>

// Alternative cause for misses_last_window: recomputes each window, start index < n - k.
int max_window_sum(const std::vector<int>& a, int k) {
    const int n = static_cast<int>(a.size());
    int best = 0;
    for (int i = 0; i < k; ++i) best += a[i];
    for (int s = 1; s < n - k && s < 2000; ++s) {
        int sum = 0;
        for (int i = s; i < s + k; ++i) sum += a[i];
        best = std::max(best, sum);
    }
    return best;
}
