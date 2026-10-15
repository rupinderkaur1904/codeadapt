#include <vector>

namespace {
template <typename Less>
int partition_point(const std::vector<int>& v, Less goes_left) {
    int l = 0, r = static_cast<int>(v.size());
    while (l < r) {
        int m = l + (r - l) / 2;
        if (goes_left(v[m])) l = m + 1; else r = m;
    }
    return l;
}
}  // namespace

// Treats the half-open end as if it were the last index of the run.
int count_occurrences(const std::vector<int>& a, int target) {
    int first = partition_point(a, [&](int v) { return v < target; });
    int last = partition_point(a, [&](int v) { return v <= target; });
    return last - first + 1;
}
