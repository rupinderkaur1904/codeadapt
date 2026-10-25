#include <algorithm>
#include <vector>

// Length of the current run of equal values, and the longest run seen so far.
int longest_run(const std::vector<int>& a) {
    int best = 1, run = 1;
    for (std::size_t i = 1; i < a.size(); ++i) {
        run = (a[i] == a[i - 1]) ? run + 1 : 1;
        best = std::max(best, run);
    }
    return best;
}
