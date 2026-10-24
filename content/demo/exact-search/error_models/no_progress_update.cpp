#include <vector>

// Sets lo = mid instead of mid + 1, so the range stops shrinking once hi == lo + 1.
int search_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) {
            lo = mid;
        } else {
            hi = mid - 1;
        }
    }
    return -1;
}
