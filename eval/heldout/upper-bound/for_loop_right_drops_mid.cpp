#include <vector>

// For-loop form; a greater element at mid moves the right edge to mid - 1.
int upper_bound_index(const std::vector<int>& a, int target) {
    int l = 0, r = static_cast<int>(a.size());
    for (; l < r;) {
        int m = (l + r) / 2;
        if (a[m] > target) r = m - 1;
        else l = m + 1;
    }
    return l;
}
