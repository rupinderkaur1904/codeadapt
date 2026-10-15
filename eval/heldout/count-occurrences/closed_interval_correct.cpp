#include <vector>

namespace {
int first_at_least(const std::vector<int>& v, int x) {
    int ans = static_cast<int>(v.size());
    int l = 0, r = static_cast<int>(v.size()) - 1;
    while (l <= r) {
        int m = l + (r - l) / 2;
        if (v[m] >= x) { ans = m; r = m - 1; } else { l = m + 1; }
    }
    return ans;
}
int first_above(const std::vector<int>& v, int x) {
    int ans = static_cast<int>(v.size());
    int l = 0, r = static_cast<int>(v.size()) - 1;
    while (l <= r) {
        int m = l + (r - l) / 2;
        if (v[m] > x) { ans = m; r = m - 1; } else { l = m + 1; }
    }
    return ans;
}
}  // namespace

// Correct: two closed-interval searches.
int count_occurrences(const std::vector<int>& a, int target) {
    return first_above(a, target) - first_at_least(a, target);
}
