#include <vector>

int longest_at_most(const std::vector<int>& a, int s) {
    long long window = 0;
    std::size_t lo = 0, best = 0;
    for (std::size_t hi = 0; hi < a.size(); ++hi) {
        window += a[hi];
        while (lo <= hi && window > s) window -= a[lo++];
        if (hi + 1 - lo > best) best = hi + 1 - lo;
    }
    return static_cast<int>(best);
}
