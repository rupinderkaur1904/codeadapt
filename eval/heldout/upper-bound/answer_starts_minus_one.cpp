#include <vector>

// Closed interval with a running answer initialised to -1 ("not found").
int upper_bound_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = -1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] > target) {
            ans = mid;
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    return ans;
}
