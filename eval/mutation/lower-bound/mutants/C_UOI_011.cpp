#include <vector>

// Recursive search over the half-open range [lo, hi).
static int search(const std::vector<int>& a, int target, int lo, int hi) {
    if (lo >= hi) {
        return (lo + 1);
    }
    const int mid = lo + (hi - lo) / 2;
    if (a[mid] < target) {
        return search(a, target, mid + 1, hi);
    }
    return search(a, target, lo, mid);
}

int lower_bound_index(const std::vector<int>& a, int target) {
    return search(a, target, 0, static_cast<int>(a.size()));
}
