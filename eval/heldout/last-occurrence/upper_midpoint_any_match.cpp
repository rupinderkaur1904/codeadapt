#include <vector>

// Closed search that returns on a match, rounding the midpoint up.
int last_occurrence(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo + 1) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}
