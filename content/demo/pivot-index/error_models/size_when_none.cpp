#include <vector>

// Error model: when no index balances, returns the loop index after the loop (n) instead of -1.
int pivot_index(const std::vector<int>& a) {
    long long total = 0;
    for (int x : a) total += x;
    long long left = 0;
    int i = 0;
    for (; i < static_cast<int>(a.size()); ++i) {
        if (left == total - left - a[i]) break;
        left += a[i];
    }
    return i;
}
