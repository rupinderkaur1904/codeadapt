#include <vector>

int longest_at_most(const std::vector<int>& a, int s) {
    long long window = 0;
    int lo = 0, best = 0;
    for (int hi = 0; hi < static_cast<int>(a.size()); ++hi) {
        window += a[hi];
        while (window > s) { window -= a[lo]; ++lo; }
        if (hi - lo > best) best = hi - lo;
    }
    return best;
}
