#include <vector>

// Two errors at once: lo starts at 1 and the insertion point is returned when absent.
int search_index(const std::vector<int>& a, int target) {
    int lo = 1, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return lo;
}
