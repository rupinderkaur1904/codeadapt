#include <vector>

// Drops mid on a 1 and also reports "no 1" as -1.
int first_true(const std::vector<int>& flags) {
    int n = flags.size();
    int lo = 0, hi = n;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 1) hi = mid - 1;
        else lo = mid + 1;
    }
    if (lo >= n) return -1;
    return lo;
}
