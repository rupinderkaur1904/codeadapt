#include <vector>

int remove_duplicates(std::vector<int>& a) {
    const int n = static_cast<int>(a.size());
    int w = 1;
    for (int r = 1; r < n - 1; ++r) {
        if (a[r] != a[w - 1]) a[w++] = a[r];
    }
    return w;
}
