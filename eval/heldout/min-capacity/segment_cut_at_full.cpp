#include <algorithm>
#include <vector>

// Closed-interval search whose check closes a day once the next package would reach the cap.
int min_capacity(const std::vector<int>& weights, int days) {
    int lo = *std::max_element(weights.begin(), weights.end()), hi = 0;
    for (int x : weights) hi += x;
    int best = hi;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        int used = 1, load = 0;
        for (int x : weights) {
            if (load + x >= mid) { ++used; load = x; }
            else load += x;
        }
        if (used <= days) { best = mid; hi = mid - 1; }
        else lo = mid + 1;
    }
    return best;
}
