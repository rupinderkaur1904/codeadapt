#include <algorithm>
#include <vector>

// Variant of last_run_unchecked with best starting at 1.
int longest_run(const std::vector<int>& a) {
    int best = 1, run = 1;
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
