#include <vector>

// Two separate loops, one per boundary; both move the left edge to the midpoint only.
int count_occurrences(const std::vector<int>& a, int target) {
    int n = static_cast<int>(a.size());
    int b = 0, e = n;
    while (b < e) {
        int m = (b + e) / 2;
        if (a[m] < target) b = m; else e = m;
    }
    int first = b;
    b = 0;
    e = n;
    while (b < e) {
        int m = (b + e) / 2;
        if (a[m] <= target) b = m; else e = m;
    }
    return b - first;
}
