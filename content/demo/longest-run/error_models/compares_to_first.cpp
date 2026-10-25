#include <algorithm>
#include <vector>

// Error model: compares each element with the first element of the array instead of its
// neighbour, so only runs equal to a[0] are extended.
int longest_run(const std::vector<int>& a) {
    int best = 1, run = 1;
    for (std::size_t i = 1; i < a.size(); ++i) {
        run = (a[i] == a[0]) ? run + 1 : 1;
        best = std::max(best, run);
    }
    return best;
}
