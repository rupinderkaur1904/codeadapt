#include <vector>

int max_window_sum(const std::vector<int>& a, int k) {
    int run = 0;
    for (int i = 0; i < k; ++i) run += a[i];
    int best = run;
    for (std::size_t i = static_cast<std::size_t>(k); i < a.size(); ++i) {
        run = run + a[i] - a[i + 1 - static_cast<std::size_t>(k)];
        if (run > best) best = run;
    }
    return best;
}
