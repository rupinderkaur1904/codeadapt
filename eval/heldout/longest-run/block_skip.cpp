#include <vector>

int longest_run(const std::vector<int>& a) {
    std::size_t best = 0, i = 0;
    while (i < a.size()) {
        std::size_t j = i;
        while (j < a.size() && a[j] == a[i]) ++j;
        if (j - i > best) best = j - i;
        i = j;
    }
    return static_cast<int>(best);
}
