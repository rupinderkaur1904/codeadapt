#include <vector>

namespace {
int search(const std::vector<int>& a, int target, int lo, int hi) {
    if (lo >= hi) return lo;
    int mid = lo + (hi - lo) / 2;
    return a[mid] < target ? search(a, target, mid + 1, hi) : search(a, target, lo, mid);
}
}  // namespace

// Recursive half-open search whose upper bound starts at the last index.
int lower_bound_index(const std::vector<int>& a, int target) {
    if (a.empty()) return 0;
    return search(a, target, 0, static_cast<int>(a.size()) - 1);
}
