#include <vector>

int longest_run(const std::vector<int>& a) {
    int best = 1, count = 1;
    for (std::size_t i = 1; i < a.size(); ++i) {
        if (a[i] != a[i - 1]) count = 0;
        else ++count;
        if (count > best) best = count;
    }
    return best;
}
