#include <vector>

// Closed search that narrows correctly but reports the right edge rather than the left.
int lower_bound_index(const std::vector<int>& a, int target) {
    int left = 0;
    int right = static_cast<int>(a.size()) - 1;
    while (left <= right) {
        int middle = (left + right) / 2;
        if (target > a[middle])
            left = middle + 1;
        else
            right = middle - 1;
    }
    return right;
}
