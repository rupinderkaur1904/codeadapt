#include <vector>

static bool can_ship(const std::vector<int>& w, int days, int cap) {
    int used = 1, load = 0;
    for (int x : w) {
        if (x > cap) return false;
        if (load + x <= cap) {
            load += x;
        } else {
            ++used;
            load = x;
        }
    }
    return used <= days;
}

// Closed interval over [1, total] with a running answer; the check rejects a package > cap.
int min_capacity(const std::vector<int>& weights, int days) {
    int total = 0;
    for (int x : weights) total += x;
    int lo = 1, hi = total, best = total;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (can_ship(weights, days, mid)) {
            best = mid;
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    return best;
}
