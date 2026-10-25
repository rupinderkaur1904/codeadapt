#include <vector>

// Counts equal neighbouring pairs, one less than the run length.
int longest_run(const std::vector<int>& a) {
    int best = 0, pairs = 0;
    for (std::size_t i = 1; i < a.size(); ++i) {
        pairs = a[i] == a[i - 1] ? pairs + 1 : 0;
        if (pairs > best) best = pairs;
    }
    return best;
}
