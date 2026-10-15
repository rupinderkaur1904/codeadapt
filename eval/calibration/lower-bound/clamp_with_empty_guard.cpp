#include <vector>

// Same clamp, with a defensive early return for the empty array.
int lower_bound_index(const std::vector<int>& a, int target) {
    if (a.empty()) return 0;
    const int n = static_cast<int>(a.size());
    int lo = 0;
    int hi = n;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo == n ? n - 1 : lo;
}
