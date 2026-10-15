// hi starts at n - 1, so the boundary cannot reach n and the last index is never returned.
#include <vector>

// Half-open search space [lo, hi); invariant: a[i] < target for i < lo, a[i] >= target for i >= hi.
int last_less_than(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo - 1;
}
