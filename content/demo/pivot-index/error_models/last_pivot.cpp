#include <vector>

// Error model: keeps scanning and returns the last balancing index instead of the first.
int pivot_index(const std::vector<int>& a) {
    long long total = 0;
    for (int x : a) total += x;
    long long left = 0;
    int found = -1;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        if (left == total - left - a[i]) found = i;
        left += a[i];
    }
    return found;
}
