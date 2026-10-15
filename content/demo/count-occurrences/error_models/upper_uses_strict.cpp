// The upper boundary uses < instead of <=, so it equals the lower boundary and the count is always 0.
#include <vector>

namespace {
// First index whose element is >= target (strict = false) or > target (strict = true).
int boundary(const std::vector<int>& a, int target, bool strict) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        const bool left = a[mid] < target;  // strict ignored
        if (left) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
}  // namespace

int count_occurrences(const std::vector<int>& a, int target) {
    return boundary(a, target, true) - boundary(a, target, false);
}
