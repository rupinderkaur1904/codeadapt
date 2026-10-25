// Correct result by linear scan: violates the O(log n) requirement.
#include <vector>

int lower_bound_index(const std::vector<int>& a, int target) {
    int i = 0;
    while (i < static_cast<int>(a.size()) && a[i] < target) ++i;
    return i;
}
