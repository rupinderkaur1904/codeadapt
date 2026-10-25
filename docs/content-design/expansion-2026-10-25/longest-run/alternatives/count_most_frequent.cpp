#include <map>
#include <vector>

// Alternative (unmodelled) error: counts the most frequent value anywhere, not consecutive runs.
int longest_run(const std::vector<int>& a) {
    std::map<int, int> c;
    int best = 0;
    for (int x : a) best = std::max(best, ++c[x]);
    return best;
}
