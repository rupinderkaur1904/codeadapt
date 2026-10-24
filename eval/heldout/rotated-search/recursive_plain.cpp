#include <vector>

static int find(const std::vector<int>& a, int target, int lo, int hi) {
    if (lo > hi) return -1;
    int mid = lo + (hi - lo) / 2;
    if (a[mid] == target) return mid;
    return target < a[mid] ? find(a, target, lo, mid - 1) : find(a, target, mid + 1, hi);
}

// Recursive ordinary binary search that ignores the rotation.
int rotated_search(const std::vector<int>& a, int target) {
    return find(a, target, 0, static_cast<int>(a.size()) - 1);
}
