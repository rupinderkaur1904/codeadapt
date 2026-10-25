#include <vector>

int longest_run(const std::vector<int>& a) {
    int best = 0, count = 0;
    for (std::size_t i = 0; i < a.size(); ++i) {
        if (i > 0 && a[i] == a[i - 1]) ++count;
        else count = 1;
        if (count > best) best = count;
    }
    return best;
}
