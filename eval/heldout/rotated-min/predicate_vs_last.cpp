#include <vector>

// Half-open search for the first element <= the array's last element.
int rotated_min_index(const std::vector<int>& a) {
    const int last = a.back();
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] <= last) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
