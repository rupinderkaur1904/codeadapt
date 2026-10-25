#include <vector>

// Two modelled errors at once: compares with the first element and returns the value.
int rotated_min_index(const std::vector<int>& a) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] >= a[lo]) lo = mid + 1;
        else hi = mid;
    }
    return a[lo];
}
