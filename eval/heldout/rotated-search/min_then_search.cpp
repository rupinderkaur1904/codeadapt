#include <vector>

static int search_run(const std::vector<int>& a, int lo, int hi, int target) {
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}

// Finds the rotation point first, then searches the one sorted run that can hold the target.
int rotated_search(const std::vector<int>& a, int target) {
    int n = static_cast<int>(a.size());
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] > a[hi]) lo = mid + 1;
        else hi = mid;
    }
    int start = lo;
    if (target >= a[start] && target <= a[n - 1]) return search_run(a, start, n - 1, target);
    return search_run(a, 0, start - 1, target);
}
