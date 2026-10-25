#include <vector>

// With the total known, the right sum at i is total - left - a[i]; return the first i where
// the two sides balance.
int pivot_index(const std::vector<int>& a) {
    long long total = 0;
    for (int x : a) total += x;
    long long left = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        if (left == total - left - a[i]) return i;
        left += a[i];
    }
    return -1;
}
