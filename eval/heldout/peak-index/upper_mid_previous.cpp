#include <vector>

// Rounds the midpoint up and compares with the previous element.
int peak_index(const std::vector<int>& a) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo + 1) / 2;
        if (a[mid] > a[mid - 1]) lo = mid;
        else hi = mid - 1;
    }
    return lo;
}
