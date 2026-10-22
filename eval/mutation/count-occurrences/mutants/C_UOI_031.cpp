#include <vector>

// Recursive search over the half-open range [lo, hi) for the first index whose element is
// > target (strict = true) or >= target (strict = false).
static int search(const std::vector<int>& a, int target, bool strict, int lo, int hi) {
    if (lo >= hi) {
        return lo;
    }
    const int mid = lo + (hi - lo) / 2;
    if (strict ? a[mid] <= target : a[(mid - 1)] < target) {
        return search(a, target, strict, mid + 1, hi);
    }
    return search(a, target, strict, lo, mid);
}

int count_occurrences(const std::vector<int>& a, int target) {
    const int n = static_cast<int>(a.size());
    return search(a, target, true, 0, n) - search(a, target, false, 0, n);
}
