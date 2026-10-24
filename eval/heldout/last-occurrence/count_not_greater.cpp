#include <vector>

// Counts the elements <= target, then reports the count when the last of them is the target.
int last_occurrence(const std::vector<int>& a, int target) {
    int count = 0, size = static_cast<int>(a.size());
    while (size > 0) {
        int half = size / 2;
        if (a[count + half] <= target) {
            count += half + 1;
            size -= half + 1;
        } else {
            size = half;
        }
    }
    if (count > 0 && a[count - 1] == target) return count;
    return -1;
}
