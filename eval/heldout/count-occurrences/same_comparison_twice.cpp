#include <vector>

namespace {
int first_index(const std::vector<int>& v, int x) {
    int l = 0, r = static_cast<int>(v.size());
    while (l < r) {
        int m = (l + r) / 2;
        if (v[m] < x) l = m + 1; else r = m;
    }
    return l;
}
}  // namespace

// Uses the same strict comparison for both ends of the run.
int count_occurrences(const std::vector<int>& a, int target) {
    int start = first_index(a, target);
    int end = first_index(a, target);
    return end - start;
}
