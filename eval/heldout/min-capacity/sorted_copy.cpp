#include <algorithm>
#include <vector>

// Works on a sorted copy of the packages, then searches the answer space.
int min_capacity(const std::vector<int>& weights, int days) {
    std::vector<int> w(weights);
    std::sort(w.begin(), w.end());
    int lo = w.back(), hi = 0;
    for (int x : w) hi += x;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        int used = 1, load = 0;
        for (int x : w) {
            if (load + x > mid) { ++used; load = 0; }
            load += x;
        }
        if (used <= days) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
