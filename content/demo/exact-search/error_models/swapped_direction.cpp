#include <vector>

// Moves the wrong way: a smaller element at mid discards the right half instead of the left.
int search_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) {
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    return -1;
}
