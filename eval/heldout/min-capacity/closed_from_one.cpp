#include <vector>

static int days_needed(const std::vector<int>& w, int cap) {
    int days = 1, load = 0;
    for (int x : w) {
        if (load + x > cap) { ++days; load = 0; }
        load += x;
    }
    return days;
}

// Closed interval with a running answer whose search starts at capacity 1.
int min_capacity(const std::vector<int>& weights, int days) {
    int total = 0;
    for (int x : weights) total += x;
    int lo = 1, hi = total, best = total;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (days_needed(weights, mid) <= days) { best = mid; hi = mid - 1; }
        else lo = mid + 1;
    }
    return best;
}
