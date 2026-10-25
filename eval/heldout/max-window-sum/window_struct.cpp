#include <climits>
#include <vector>

int max_window_sum(const std::vector<int>& a, int k) {
    int best = INT_MIN, run = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        run += a[i];
        if (i >= k) run -= a[i - k];
        if (i >= k - 1 && run > best) best = run;
    }
    return best;
}
