#include <vector>

int lower_bound_index(const std::vector<int>& a, int target) {
    int l = 0, r = static_cast<int>(a.size()) - 1;
    while (!(l > r)) {
        int m = (l + r) / 2;
        if (a[m] >= target)
            r = m;
        else
            l = m + 1;
    }
    return l;
}
