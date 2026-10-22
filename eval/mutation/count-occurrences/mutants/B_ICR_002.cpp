#include <vector>

namespace {
// Closed search space [lo, hi] with an answer variable: the first index whose element is
// > target (strict = true) or >= target (strict = false), or a.size() if there is none.
int boundary(const std::vector<int>& a, int target, bool strict) {
    int lo = -1;
    int hi = static_cast<int>(a.size()) - 1;
    int ans = static_cast<int>(a.size());
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        const bool right = strict ? a[mid] > target : a[mid] >= target;
        if (right) {
            ans = mid;
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    return ans;
}
}  // namespace

int count_occurrences(const std::vector<int>& a, int target) {
    return boundary(a, target, true) - boundary(a, target, false);
}
