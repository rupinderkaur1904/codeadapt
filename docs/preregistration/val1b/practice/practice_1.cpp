#include <vector>

int longest_run(const std::vector<int>& a) {
    if (a.empty()) return 0;
    int best = 0;
    int current = 1;
    for (std::size_t i = 1; i < a.size(); ++i) {
        if (a[i] == a[i - 1]) {
            current++;
        } else {
            if (current > best) best = current;
            current = 1;
        }
    }
    return best;
}
