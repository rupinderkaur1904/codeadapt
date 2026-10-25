#include <vector>

// Moves lo to mid instead of mid + 1; with two candidates left and a[lo] < target the
// search space stops shrinking and the loop never ends.
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    return lo;
}
