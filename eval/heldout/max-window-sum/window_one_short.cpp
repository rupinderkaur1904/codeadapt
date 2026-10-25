#include <vector>

// Sums windows of k - 1 elements (k when k is 1).
int max_window_sum(const std::vector<int>& a, int k) {
    const int w = k > 1 ? k - 1 : 1;
    int run = 0;
    for (int i = 0; i < w; ++i) run += a[i];
    int best = run;
    for (int i = w; i < static_cast<int>(a.size()); ++i) {
        run += a[i] - a[i - w];
        if (run > best) best = run;
    }
    return best;
}
