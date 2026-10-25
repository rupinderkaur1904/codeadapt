#include <vector>

// Alternative (unmodelled) error: never considers the first or last index as a pivot.
int pivot_index(const std::vector<int>& a) {
    long long total = 0;
    for (int x : a) total += x;
    long long left = a.empty() ? 0 : a[0];
    for (int i = 1; i + 1 < static_cast<int>(a.size()); ++i) {
        if (left == total - left - a[i]) return i;
        left += a[i];
    }
    return -1;
}
