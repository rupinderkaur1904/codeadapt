#include <algorithm>
#include <vector>

// Error model: adds each entering element but never subtracts the leaving one, so the "window"
// keeps growing from the start.
int max_window_sum(const std::vector<int>& a, int k) {
    int sum = 0;
    for (int i = 0; i < k; ++i) sum += a[i];
    int best = sum;
    for (int i = k; i < static_cast<int>(a.size()); ++i) {
        sum += a[i];
        best = std::max(best, sum);
    }
    return best;
}
