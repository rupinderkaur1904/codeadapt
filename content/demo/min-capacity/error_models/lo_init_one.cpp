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

// Starts the search at capacity 1 instead of the heaviest package, so a capacity below some package can be accepted.
int min_capacity(const std::vector<int>& weights, int days) {
    int lo = 1, hi = 0;
    for (int x : weights) hi += x;
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
