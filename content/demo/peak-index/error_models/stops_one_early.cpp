#include <vector>

// Loops while hi - lo > 1 and returns lo, so when two candidates remain the right one is never considered.
int peak_index(const std::vector<int>& a) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (hi - lo > 1) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < a[mid + 1]) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
