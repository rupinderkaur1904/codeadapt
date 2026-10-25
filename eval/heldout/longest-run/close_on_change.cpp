#include <vector>

int longest_run(const std::vector<int>& a) {
    int best = 0, count = 1;
    int prev = a[0];
    for (std::size_t i = 1; i < a.size(); ++i) {
        if (a[i] == prev) {
            count += 1;
            continue;
        }
        if (count > best) best = count;
        count = 1;
        prev = a[i];
    }
    return best;
}
