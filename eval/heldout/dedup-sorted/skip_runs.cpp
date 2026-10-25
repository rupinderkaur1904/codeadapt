#include <vector>

int remove_duplicates(std::vector<int>& a) {
    std::size_t w = 0, r = 0;
    while (r < a.size()) {
        const int v = a[r];
        a[w++] = v;
        while (r < a.size() && a[r] == v) ++r;
    }
    return static_cast<int>(w);
}
