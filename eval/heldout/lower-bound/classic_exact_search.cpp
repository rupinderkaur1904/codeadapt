#include <vector>

// Textbook exact-match search: index of some occurrence, or -1 when absent.
int lower_bound_index(const std::vector<int>& a, int target) {
    int left = 0;
    int right = static_cast<int>(a.size()) - 1;
    while (left <= right) {
        int middle = (left + right) / 2;
        if (a[middle] == target) return middle;
        if (a[middle] < target) left = middle + 1;
        else right = middle - 1;
    }
    return -1;
}
