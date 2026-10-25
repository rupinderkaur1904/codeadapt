#include <vector>

// Keeps up to two copies of each value.
int remove_duplicates(std::vector<int>& a) {
    int w = 0;
    for (std::size_t r = 0; r < a.size(); ++r) {
        if (w < 2 || a[r] != a[w - 2]) a[w++] = a[r];
    }
    return w;
}
