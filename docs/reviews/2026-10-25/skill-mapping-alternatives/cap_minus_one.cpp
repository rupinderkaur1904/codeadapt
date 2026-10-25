#include <algorithm>
#include <vector>

static int days_needed(const std::vector<int>& w, int cap) {
    int days = 1, load = 0;
    for (int x : w) {
        if (load + x > cap - 1) { ++days; load = 0; }
        load += x;
    }
    return days;
}

// Alternative cause for full_day_overflows: treats the usable capacity as cap - 1 (misreads the capacity).
int min_capacity(const std::vector<int>& weights, int days) {
    int lo = 0, hi = 0;
    for (int x : weights) { lo = std::max(lo, x); hi += x; }
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (days_needed(weights, mid) <= days) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    return lo;
}
