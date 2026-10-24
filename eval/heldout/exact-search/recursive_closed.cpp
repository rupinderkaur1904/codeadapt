#include <vector>

static int find(const std::vector<int>& a, int target, int lo, int hi) {
    if (lo > hi) return -1;
    int mid = lo + (hi - lo) / 2;
    if (a[mid] == target) return mid;
    return a[mid] < target ? find(a, target, mid + 1, hi) : find(a, target, lo, mid - 1);
}

// Recursive closed-interval search.
int search_index(const std::vector<int>& a, int target) {
    return find(a, target, 0, static_cast<int>(a.size()) - 1);
}
