#include <algorithm>
#include <vector>

int longest_run(const std::vector<int>& a) {
    int best = 0;
    int current = 0;
    for (std::size_t i = 0; i < a.size(); ++i) {
        current = (i > 0 && a[i] == a[i - 1]) ? current + 1 : 1;
        best = std::max(best, current);
    }
    return best;
}
