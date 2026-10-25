#include <vector>

// Error model: the read loop stops one element early, so a new value in the last position is
// lost.
int remove_duplicates(std::vector<int>& a) {
    int k = 1;
    for (std::size_t i = 1; i + 1 < a.size(); ++i) {
        if (a[i] != a[k - 1]) a[k++] = a[i];
    }
    return k;
}
