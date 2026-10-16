#include <vector>

// Half-open loop, but the else branch sets hi = mid - 1 instead of hi = mid, discarding
// a[mid], which may itself be the answer.
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return lo;
}
