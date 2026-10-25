#include <vector>

// Alternative cause for returns_last_index: correct compaction, then returns k - 1.
int remove_duplicates(std::vector<int>& a) {
    int k = 1;
    for (std::size_t i = 1; i < a.size(); ++i) if (a[i] != a[k - 1]) a[k++] = a[i];
    return k - 1;
}
