#include <vector>

// Closed-interval loop (lo <= hi) with hi = n: when the target is larger than every
// element the search probes a[n], one past the end. Undefined behaviour; the standard
// build may still print the right answer, depending on what lies past the array.
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size());
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return lo;
}
