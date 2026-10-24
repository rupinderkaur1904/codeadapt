#include <algorithm>
#include <vector>

// Correct search, but the check lets a day exceed the capacity by one unit.
int min_capacity(const std::vector<int>& weights, int days) {
    int lo = *std::max_element(weights.begin(), weights.end()), hi = 0;
    for (int x : weights) hi += x;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        int used = 1, load = 0;
        for (int x : weights) {
            if (load + x > mid + 1) { ++used; load = 0; }
            load += x;
        }
        if (used <= days) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
