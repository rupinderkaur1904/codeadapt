#include <algorithm>
#include <vector>

static int days_needed(const std::vector<int>& w, int cap) {
    int days = 1, load = 0;
    for (int x : w) {
        if (load + x > cap) { ++days; load = 0; }
        load += x;
    }
    return days;
}

// Sets lo = mid instead of mid + 1 after an infeasible capacity, so the range stops shrinking.
int min_capacity(const std::vector<int>& weights, int days) {
    int lo = 0, hi = 0;
    for (int x : weights) { lo = std::max(lo, x); hi += x; }
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (days_needed(weights, mid) <= days) {
            hi = mid;
        } else {
            lo = mid;
        }
    }
    return lo;
}
