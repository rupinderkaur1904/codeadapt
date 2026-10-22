#include <vector>

// Closed search space [lo, hi] with an answer variable: ans holds the smallest index seen so
// far with flags[i] == 1, or flags.size() if there is none.
int first_true(const std::vector<int>& flags) {
    int lo = 1;
    int hi = static_cast<int>(flags.size()) - 1;
    int ans = static_cast<int>(flags.size());
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 1) {
            ans = mid;
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    return ans;
}
