#include <vector>

// Outside the modelled errors: reports whether the target occurs (1) or not (0).
int count_occurrences(const std::vector<int>& a, int target) {
    int l = 0, r = static_cast<int>(a.size()) - 1;
    while (l <= r) {
        int m = l + (r - l) / 2;
        if (a[m] == target) return 1;
        if (a[m] < target) l = m + 1; else r = m - 1;
    }
    return 0;
}
