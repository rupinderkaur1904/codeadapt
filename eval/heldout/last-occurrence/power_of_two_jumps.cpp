#include <vector>

// Moves a position right by decreasing powers of two while the element there is <= target.
int last_occurrence(const std::vector<int>& a, int target) {
    const int n = static_cast<int>(a.size());
    int pos = -1;  // last index known to hold a value <= target
    for (int step = 1 << 30; step > 0; step >>= 1) {
        if (pos + step < n && a[pos + step] <= target) pos += step;
    }
    return (pos >= 0 && a[pos] == target) ? pos : -1;
}
