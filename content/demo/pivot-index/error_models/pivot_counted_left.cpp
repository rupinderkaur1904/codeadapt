#include <vector>

// Error model: adds a[i] to the left sum before comparing, so the pivot is counted on the left.
int pivot_index(const std::vector<int>& a) {
    long long total = 0;
    for (int x : a) total += x;
    long long left = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        left += a[i];
        if (left == total - left) return i;
    }
    return -1;
}
