#include <map>
#include <vector>

// Counts occurrences anywhere, not consecutive runs.
int longest_run(const std::vector<int>& a) {
    std::map<int, int> seen;
    int best = 0;
    for (int x : a) if (++seen[x] > best) best = seen[x];
    return best;
}
