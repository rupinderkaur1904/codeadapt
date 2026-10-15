#include <vector>

// Two modelled bugs at once (<= and clamping to 0): outside the single-error model space.
int last_less_than(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) lo = mid + 1; else hi = mid;
    }
    return lo > 0 ? lo - 1 : 0;
}
