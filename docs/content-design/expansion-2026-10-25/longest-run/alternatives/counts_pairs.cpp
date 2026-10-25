#include <algorithm>
#include <vector>

// Alternative accumulator error: counts equal neighbouring pairs (start and reset at 0).
int longest_run(const std::vector<int>& a) {
    int best = 0, run = 0;
    for (std::size_t i = 1; i < a.size(); ++i) {
        run = (a[i] == a[i - 1]) ? run + 1 : 0;
        best = std::max(best, run);
    }
    return best;
}
