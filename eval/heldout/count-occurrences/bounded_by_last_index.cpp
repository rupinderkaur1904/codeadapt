#include <vector>

namespace {
int boundary_ge(const std::vector<int>& v, int x) {
    int l = 0, r = static_cast<int>(v.size()) - 1;
    while (l < r) {
        int m = l + (r - l) / 2;
        if (v[m] < x) l = m + 1; else r = m;
    }
    return l < 0 ? 0 : l;
}
int boundary_gt(const std::vector<int>& v, int x) {
    int l = 0, r = static_cast<int>(v.size()) - 1;
    while (l < r) {
        int m = l + (r - l) / 2;
        if (v[m] <= x) l = m + 1; else r = m;
    }
    return l < 0 ? 0 : l;
}
}  // namespace

// Both searches start with r = size - 1, so neither can return size().
int count_occurrences(const std::vector<int>& a, int target) {
    return boundary_gt(a, target) - boundary_ge(a, target);
}
