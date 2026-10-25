#include <vector>

// Initialises lo = 1, so index 0 is never a candidate.
int search_index(const std::vector<int>& a, int target) {
    int lo = 1;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return -1;
}
