#include <vector>
// Alternative cause for compares_with_lo: assumes the array IS rotated and searches for the first element smaller than a[0] (the "drop").
int rotated_min_index(const std::vector<int>& a) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] >= a[0]) lo = mid + 1; else hi = mid;
    }
    return lo;
}
