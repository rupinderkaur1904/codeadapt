#include <algorithm>
#include <vector>

// Error model: the best length is updated only when a run ends, so the final run is never
// compared.
int longest_run(const std::vector<int>& a) {
    int best = 0, run = 1;
    for (std::size_t i = 1; i < a.size(); ++i) {
        if (a[i] == a[i - 1]) {
            ++run;
        } else {
            best = std::max(best, run);
            run = 1;
        }
    }
    return best;
}
