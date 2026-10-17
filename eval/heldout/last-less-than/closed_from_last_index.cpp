#include <vector>

// Searches for the first element >= target in [0, n - 1] only, then steps back one.
int last_less_than(const std::vector<int>& a, int target) {
    int n = static_cast<int>(a.size());
    int low = 0, high = n - 1;
    int firstNotLess = n - 1 < 0 ? 0 : n - 1;
    while (low < high) {
        int mid = (low + high) / 2;
        if (!(a[mid] < target)) high = mid; else low = mid + 1;
    }
    firstNotLess = low;
    return firstNotLess - 1;
}
