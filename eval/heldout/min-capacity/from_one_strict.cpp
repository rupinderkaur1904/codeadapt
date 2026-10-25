#include <vector>

// Two modelled errors at once: the search starts at 1 and needs strictly fewer days.
int min_capacity(const std::vector<int>& weights, int days) {
    int lo = 1, hi = 0;
    for (int x : weights) hi += x;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        int used = 1, load = 0;
        for (int x : weights) {
            if (load + x > mid) { ++used; load = 0; }
            load += x;
        }
        if (used < days) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
