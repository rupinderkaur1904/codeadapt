#include <vector>

int closest_pair_gap(const std::vector<int>& a, int target) {
    std::size_t i = 0, j = a.size() - 1;
    long long best = -1;
    while (i < j) {
        const long long d = static_cast<long long>(a[i]) + a[j] - target;
        const long long g = d < 0 ? -d : d;
        if (best < 0 || g < best) best = g;
        if (d < 0) ++i;
        else if (d > 0) --j;
        else break;
    }
    return static_cast<int>(best);
}
