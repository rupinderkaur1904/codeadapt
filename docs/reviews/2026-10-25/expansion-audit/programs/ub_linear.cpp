#include <vector>
int upper_bound_index(const std::vector<int>& a, int target) {
    int i = 0;
    while (i < (int)a.size() && a[i] <= target) ++i;
    return i;
}
