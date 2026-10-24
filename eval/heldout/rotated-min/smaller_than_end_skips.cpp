#include <vector>

// Moves hi below mid whenever mid is smaller than the end of the range.
int rotated_min_index(const std::vector<int>& a) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] < a[hi]) hi = mid - 1;
        else lo = mid + 1;
    }
    return lo;
}
