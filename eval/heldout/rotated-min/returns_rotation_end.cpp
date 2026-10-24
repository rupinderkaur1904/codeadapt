#include <vector>

// Finds the minimum, then reports the position just before it (wrapping to the end).
int rotated_min_index(const std::vector<int>& a) {
    int n = static_cast<int>(a.size());
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] > a[hi]) lo = mid + 1;
        else hi = mid;
    }
    return lo == 0 ? n - 1 : lo - 1;
}
