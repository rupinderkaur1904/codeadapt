#include <vector>

// For-loop form over a closed range that runs while left < right.
int search_index(const std::vector<int>& a, int target) {
    for (int left = 0, right = static_cast<int>(a.size()) - 1; left < right;) {
        int m = left + (right - left) / 2;
        if (a[m] < target) left = m + 1;
        else if (a[m] > target) right = m - 1;
        else return m;
    }
    return -1;
}
