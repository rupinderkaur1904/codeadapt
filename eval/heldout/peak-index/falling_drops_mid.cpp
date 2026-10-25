#include <vector>

// Drops mid from the range whenever the next element is smaller.
int peak_index(const std::vector<int>& a) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] > a[mid + 1]) hi = mid - 1;
        else lo = mid + 1;
    }
    return lo;
}
