#include <vector>

// Comparison written target-first; the "go left" branch also discards the middle.
int lower_bound_index(const std::vector<int>& a, int target) {
    int left = 0, right = static_cast<int>(a.size());
    while (right > left) {
        int m = left + (right - left) / 2;
        if (target <= a[m])
            right = m - 1;
        else
            left = m + 1;
    }
    return left;
}
