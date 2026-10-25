#include <vector>

int max_window_sum(const std::vector<int>& a, int k) {
    std::vector<int> p(a.size() + 1, 0);
    for (std::size_t i = 0; i < a.size(); ++i) p[i + 1] = p[i] + a[i];
    int best = 0;
    for (std::size_t end = static_cast<std::size_t>(k); end <= a.size(); ++end)
        if (p[end] - p[end - k] > best) best = p[end] - p[end - k];
    return best;
}
