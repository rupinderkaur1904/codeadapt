#include <vector>

int max_window_sum(const std::vector<int>& a, int k) {
    int run = 0, best = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        run += a[i];
        if (i == k - 1) best = run;
        else if (i >= k && run > best) best = run;
    }
    return best;
}
