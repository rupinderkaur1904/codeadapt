#include <vector>

// Error model: k is the index of the last kept element and is returned as is, so the count is
// one too small.
int remove_duplicates(std::vector<int>& a) {
    int k = 0;
    for (std::size_t i = 1; i < a.size(); ++i) {
        if (a[i] != a[k]) a[++k] = a[i];
    }
    return k;
}
