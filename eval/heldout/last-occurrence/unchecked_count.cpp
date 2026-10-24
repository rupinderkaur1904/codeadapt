#include <vector>

// Returns the number of elements <= target with no equality check: two modelled errors at once.
int last_occurrence(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] > target) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
