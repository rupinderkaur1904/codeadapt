#include <vector>

// Goes right when the next element is smaller.
int peak_index(const std::vector<int>& a) {
    int left = 0, right = static_cast<int>(a.size()) - 1;
    while (left < right) {
        int mid = (left + right) / 2;
        if (a[mid + 1] < a[mid]) left = mid + 1;
        else right = mid;
    }
    return left;
}
