#include <vector>

// The window never shrinks below the best length found so far.
int longest_at_most(const std::vector<int>& a, int s) {
    long long window = 0;
    int lo = 0;
    for (int hi = 0; hi < static_cast<int>(a.size()); ++hi) {
        window += a[hi];
        if (window > s) window -= a[lo++];
    }
    return static_cast<int>(a.size()) - lo;
}
