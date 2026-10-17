#include <vector>

int last_less_than(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (true) {
        if (hi - lo <= 0) return lo - 1;
        int mid = (lo + hi) >> 1;
        if (target > a[mid])
            lo = mid;
        else
            hi = mid;
    }
}
