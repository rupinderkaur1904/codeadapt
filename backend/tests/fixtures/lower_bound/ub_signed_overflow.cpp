#include <climits>
#include <vector>

// Signed overflow on every call: target + INT_MAX overflows for any positive target.
int lower_bound_index(const std::vector<int>& a, int target) {
    volatile int bias = INT_MAX;
    const int shifted = target + bias;  // undefined behaviour for target > 0
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] + bias < shifted) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
