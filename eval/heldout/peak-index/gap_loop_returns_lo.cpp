#include <vector>

// Stops once lo and hi are adjacent and reports lo.
int peak_index(const std::vector<int>& a) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    for (; lo + 1 < hi;) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] < a[mid + 1]) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
