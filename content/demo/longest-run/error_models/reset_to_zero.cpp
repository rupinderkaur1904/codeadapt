#include <algorithm>
#include <vector>

// Error model: a new run restarts its length at 0 instead of 1, so every run after the first is
// counted one too short.
int longest_run(const std::vector<int>& a) {
    int best = 1, run = 1;
    for (std::size_t i = 1; i < a.size(); ++i) {
        run = (a[i] == a[i - 1]) ? run + 1 : 0;
        best = std::max(best, run);
    }
    return best;
}
