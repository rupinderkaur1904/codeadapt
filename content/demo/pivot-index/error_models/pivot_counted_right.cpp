#include <vector>

// Error model: the right sum is total - left, so the pivot is counted on the right.
int pivot_index(const std::vector<int>& a) {
    long long total = 0;
    for (int x : a) total += x;
    long long left = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        if (left == total - left) return i;
        left += a[i];
    }
    return -1;
}
