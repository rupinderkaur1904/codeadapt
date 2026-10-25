#include <vector>

// Alternative (unmodelled) error: returns 0 when nothing balances.
int pivot_index(const std::vector<int>& a) {
    long long total = 0, left = 0;
    for (int x : a) total += x;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        if (left == total - left - a[i]) return i;
        left += a[i];
    }
    return 0;
}
