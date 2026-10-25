#include <vector>

// Alternative cause for last_pivot: scans from the right and returns the first balance found.
int pivot_index(const std::vector<int>& a) {
    long long total = 0;
    for (int x : a) total += x;
    long long right = 0;
    for (int i = static_cast<int>(a.size()) - 1; i >= 0; --i) {
        if (right == total - right - a[i]) return i;
        right += a[i];
    }
    return -1;
}
