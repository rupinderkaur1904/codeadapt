#include <vector>

// Searches positions 0..n-1 of the unrotated order (offset by the rotation) and returns the
// position it searched, not the array index.
int rotated_search(const std::vector<int>& a, int target) {
    int n = static_cast<int>(a.size());
    int left = 0, right = n - 1;
    while (left < right) {
        int mid = (left + right) / 2;
        if (a[mid] > a[right]) left = mid + 1;
        else right = mid;
    }
    int offset = left;
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int pos = (lo + hi) / 2;
        int v = a[(pos + offset) % n];
        if (v == target) return pos;
        if (v < target) lo = pos + 1;
        else hi = pos - 1;
    }
    return -1;
}
