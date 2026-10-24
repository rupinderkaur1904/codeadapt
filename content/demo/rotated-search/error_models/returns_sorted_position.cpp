#include <vector>

// Finds the rotation, searches the array as if unrotated, and returns the position in the
// sorted order instead of the index in a.
int rotated_search(const std::vector<int>& a, int target) {
    const int n = static_cast<int>(a.size());
    int lo = 0;
    int hi = n - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] > a[hi]) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    const int shift = lo;
    lo = 0;
    hi = n - 1;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        const int value = a[(mid + shift) % n];
        if (value == target) return mid;
        if (value < target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return -1;
}
