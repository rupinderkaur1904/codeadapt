#include <vector>

static int find_min(const std::vector<int>& a, int lo, int hi) {
    if (lo == hi || a[lo] < a[hi]) return lo;  // single element, or a sorted range
    int mid = lo + (hi - lo) / 2;
    if (a[mid] > a[hi]) return find_min(a, mid + 1, hi);
    return find_min(a, lo, mid);
}

// Recursive search that stops early on a sorted range.
int rotated_min_index(const std::vector<int>& a) {
    return find_min(a, 0, static_cast<int>(a.size()) - 1);
}
