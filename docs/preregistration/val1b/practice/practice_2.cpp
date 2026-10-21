#include <vector>

int longest_run(const std::vector<int>& a) {
    int best = 0;
    int current = 0;
    for (std::size_t i = 0; i < a.size(); ++i) {
        if (i > 0 && a[i] == a[i - 1]) {
            current++;
        } else {
            current = 0;
        }
        if (current > best) best = current;
    }
    return best;
}
