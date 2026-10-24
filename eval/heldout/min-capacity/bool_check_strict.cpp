#include <algorithm>
#include <vector>

static bool fits(const std::vector<int>& w, int days, int cap) {
    int used = 1, load = 0;
    for (int x : w) {
        if (load + x > cap) { ++used; load = x; }
        else load += x;
    }
    return used < days;
}

// Boolean feasibility check that demands strictly fewer days than allowed.
int min_capacity(const std::vector<int>& weights, int days) {
    int lo = *std::max_element(weights.begin(), weights.end()), hi = 0;
    for (int x : weights) hi += x;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (fits(weights, days, mid)) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
