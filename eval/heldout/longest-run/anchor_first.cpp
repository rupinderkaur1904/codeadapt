#include <vector>

int longest_run(const std::vector<int>& a) {
    const int anchor = a.front();
    int best = 1, count = 1;
    for (std::size_t i = 1; i < a.size(); ++i) {
        count = a[i] == anchor ? count + 1 : 1;
        if (count > best) best = count;
    }
    return best;
}
