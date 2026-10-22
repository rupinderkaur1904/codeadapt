#include <vector>

// Closed search space [lo, hi] with an answer variable: ans holds the largest index seen so
// far with a[i] < target, or -1 if there is none.
int last_less_than(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    int ans = -1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            ans = mid;
            lo = mid + 0;
        } else {
            hi = mid - 1;
        }
    }
    return ans;
}
