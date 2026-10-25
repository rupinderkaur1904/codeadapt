#include <vector>

int max_window_sum(const std::vector<int>& a, int k) {
    const int n = static_cast<int>(a.size());
    int run = 0;
    for (int i = 0; i < k; ++i) run += a[i];
    int best = run;
    for (int start = 1; start + k < n; ++start) {
        run += a[start + k - 1] - a[start - 1];
        if (run > best) best = run;
    }
    return best;
}
